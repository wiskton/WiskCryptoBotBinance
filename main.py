import os
import sys
import time
import schedule
import math
import pandas as pd
from dotenv import load_dotenv
from binance.client import Client
import ta
from utils.telegram import send_telegram
from utils.discord import send_discord
from utils.util import log

# ========== INICIALIZAÇÃO ==========
load_dotenv()

# ========== CONFIG DE MOEDAS ==========
CONFIGS = {
    'BTCUSDT': {'leverage': 20, 'risk_percent': 0.05, 'direction': 'LONG'},
    'ETHUSDT': {'leverage': 10, 'risk_percent': 0.05, 'direction': 'LONG'},
    'PENDLEUSDT': {'leverage': 5, 'risk_percent': 0.05, 'direction': 'BOTH'},
    'VIRTUALUSDT': {'leverage': 5, 'risk_percent': 0.05, 'direction': 'BOTH'},
    'PNUTUSDT': {'leverage': 5, 'risk_percent': 0.05, 'direction': 'SHORT'},
}
SYMBOLS = list(CONFIGS.keys())

# ========== CONFIG ==========
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

STOP_LOOKBACK = 20      # candle lookback para stop

# ========== ESTADO GLOBAL ==========
positions_state = {}
# Estrutura:
# positions_state = {
#    'BTCUSDT': {
#       'open': False,
#       'side': None,
#       'stop_loss': None,
#       'qty': 0.0,
#    },
#    ...
# }

# ========== CLIENTE BINANCE ==========
client = Client(API_KEY, API_SECRET)

def get_klines(symbol, interval='1h', limit=100):
    try:
        klines = client.futures_klines(symbol=symbol, interval=interval, limit=limit)
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_volume', 'taker_buy_quote_volume', 'ignore'
        ])
        df['close'] = pd.to_numeric(df['close'])
        df['low'] = pd.to_numeric(df['low'])
        df['high'] = pd.to_numeric(df['high'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except Exception as e:
        log(f"Erro ao obter klines {symbol} {interval}: {e}")
        return pd.DataFrame()

def get_usdt_balance():
    try:
        balance = client.futures_account_balance()
        for asset in balance:
            if asset['asset'] == 'USDT':
                return float(asset['balance'])
    except Exception as e:
        log(f"Erro ao obter saldo USDT: {e}")
    return 0.0

def get_available_margin():
    try:
        data = client.futures_account()
        for asset in data['assets']:
            if asset['asset'] == 'USDT':
                return float(asset['availableBalance'])
    except Exception as e:
        log(f"Erro ao obter margem disponível: {e}")
    return 0.0

def get_symbol_info(symbol):
    try:
        info = client.futures_exchange_info()
        for s in info['symbols']:
            if s['symbol'] == symbol:
                return s
    except Exception as e:
        log(f"Erro ao obter info do símbolo {symbol}: {e}")
    return None

def get_min_qty(symbol):
    info = get_symbol_info(symbol)
    if not info:
        return 0.001  # valor padrão seguro
    for filt in info['filters']:
        if filt['filterType'] == 'LOT_SIZE':
            min_qty = float(filt['minQty'])
            return min_qty
    return 0.001

def round_qty(qty, symbol):
    min_qty = get_min_qty(symbol)
    # Ajusta a quantidade para ser no mínimo min_qty e arredondada para DECIMALS
    qty = max(qty, min_qty)
    qty = round(qty, DECIMALS)
    # Garante que qty é múltiplo de min_qty
    # Evita problemas de ordens inválidas
    remainder = qty % min_qty
    if remainder != 0:
        qty = qty - remainder
        if qty < min_qty:
            qty = min_qty
    return qty

# ========== LÓGICA DE RISCO ==========
def calculate_risk_quantity(symbol, entry_price, stop_loss_price, risk_usdt):
    price_diff = abs(entry_price - stop_loss_price)
    if price_diff == 0:
        log("❌ Diferença entre preço de entrada e stop é zero.")
        return 0
    qty = risk_usdt / price_diff
    qty = round_qty(qty, symbol)
    return qty

# ========== LÓGICA DE SINAIS ==========
def check_rsi_trigger(symbol):
    # RSI no gráfico 15m, verificar se <=30 para LONG ou >=70 para SHORT
    try:
        df = get_klines(symbol, interval='15m', limit=100)
        if df.empty:
            return False, False
        df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
        last_rsi = df['rsi'].iloc[-1]
        rsi_long = last_rsi <= 30
        rsi_short = last_rsi >= 70
        return rsi_long, rsi_short
    except Exception as e:
        log(f"Erro ao calcular RSI trigger {symbol}: {e}")
        return False, False

def check_ma_crossover(symbol):
    # Cruzamento MA9 e MA21 no gráfico 3m
    try:
        df = get_klines(symbol, interval='3m', limit=30)
        if df.empty or len(df) < 22:
            return None
        df['ma9'] = df['close'].rolling(window=9).mean()
        df['ma21'] = df['close'].rolling(window=21).mean()

        ma9_prev = df['ma9'].iloc[-2]
        ma21_prev = df['ma21'].iloc[-2]
        ma9_curr = df['ma9'].iloc[-1]
        ma21_curr = df['ma21'].iloc[-1]

        if ma9_prev < ma21_prev and ma9_curr > ma21_curr:
            return 'LONG'
        elif ma9_prev > ma21_prev and ma9_curr < ma21_curr:
            return 'SHORT'
        else:
            return None
    except Exception as e:
        log(f"Erro ao calcular crossover {symbol}: {e}")
        return None

# ========== LÓGICA DE OPERAÇÃO ==========
def place_order(symbol, side, risk_usdt):
    global positions_state

    try:
        leverage = CONFIGS.get(symbol, {}).get('leverage', LEVERAGE)
        client.futures_change_leverage(symbol=symbol, leverage=leverage)
    except Exception as e:
        log(f"Erro ao alterar alavancagem para {symbol}: {e}")

    try:
        entry_price = float(client.futures_symbol_ticker(symbol=symbol)['price'])
    except Exception as e:
        log(f"Erro ao obter preço atual {symbol}: {e}")
        return False

    # Busca candles 3m para stop loss
    df = get_klines(symbol, interval='3m', limit=STOP_LOOKBACK)
    if df.empty or len(df) < STOP_LOOKBACK:
        log(f"Dados insuficientes para stop loss {symbol}")
        return False

    stop_loss_price = df['low'].min() if side == 'LONG' else df['high'].max()

    risk_percent = CONFIGS.get(symbol, {}).get('risk_percent', RISK_PERCENT)
    risk_usdt = get_usdt_balance() * risk_percent
    qty = calculate_risk_quantity(symbol, entry_price, stop_loss_price, risk_usdt)
    if qty <= 0:
        log(f"Quantidade calculada inválida para {symbol}: {qty}")
        return False

    try:
        # Ordem mercado
        order_entry = client.futures_create_order(
            symbol=symbol,
            side='BUY' if side == 'LONG' else 'SELL',
            type='MARKET',
            quantity=qty
        )
        if 'orderId' not in order_entry:
            log(f"Falha na ordem de entrada {symbol}: {order_entry}")
            return False
    except Exception as e:
        log(f"Erro ao criar ordem de entrada {symbol}: {e}")
        return False

    # Ajuste do preço do stop para ordem stop_market
    stop_price = round(stop_loss_price * (0.999 if side == 'LONG' else 1.001), 2)

    try:
        # Ordem stop loss
        order_stop = client.futures_create_order(
            symbol=symbol,
            side='SELL' if side == 'LONG' else 'BUY',
            type='STOP_MARKET',
            stopPrice=str(stop_price),
            closePosition=True,
            timeInForce='GTC'
        )
        if 'orderId' not in order_stop:
            log(f"Falha na ordem de stop loss {symbol}: {order_stop}")
            return False
    except Exception as e:
        log(f"Erro ao criar ordem de stop loss {symbol}: {e}")
        return False

    # Ordem Take Profit
    take_profit_price = round(entry_price * (1.015 if side == 'LONG' else 0.985), get_price_decimals(symbol))
    try:
        order_tp = client.futures_create_order(
            symbol=symbol,
            side='SELL' if side == 'LONG' else 'BUY',
            type='TAKE_PROFIT_MARKET',
            stopPrice=str(take_profit_price),
            closePosition=True,
            timeInForce='GTC'
        )
        if 'orderId' not in order_tp:
            log(f"Falha na ordem de take profit {symbol}: {order_tp}")
            return False
    except Exception as e:
        log(f"Erro ao criar ordem de take profit {symbol}: {e}")
        return False

    # Atualiza estado
    positions_state[symbol] = {
        'open': True,
        'side': side,
        'stop_loss': stop_loss_price,
        'qty': qty,
    }

    log(f"🟢 {symbol} {side} aberto | Entrada: {entry_price} | Qtd: {qty} | SL: {stop_price}")
    send_telegram(f"🚀 {symbol} {side} aberto em {entry_price}\nSL: {stop_price}")
    send_discord(f"🚀 {symbol} {side} aberto em {entry_price}\nSL: {stop_price}")

    return True

def cancel_open_stop_orders(symbol):
    try:
        open_orders = client.futures_get_open_orders(symbol=symbol)
        for order in open_orders:
            if order['type'] == 'STOP_MARKET':
                client.futures_cancel_order(symbol=symbol, orderId=order['orderId'])
                log(f"🗑️ Ordem STOP_MARKET cancelada para {symbol}: ID {order['orderId']}")
    except Exception as e:
        log(f"Erro ao cancelar ordens stop {symbol}: {e}")

def get_price_decimals(symbol):
    info = get_symbol_info(symbol)
    if not info:
        return 2  # fallback seguro
    for filt in info['filters']:
        if filt['filterType'] == 'PRICE_FILTER':
            tick_size = float(filt['tickSize'])
            # Conta quantos zeros existem após a vírgula
            decimals = abs(int(round(math.log10(tick_size))))
            return decimals
    return 2


def update_stop_loss(symbol):
    if symbol not in positions_state or not positions_state[symbol]['open']:
        return

    side = positions_state[symbol]['side']
    old_stop = positions_state[symbol]['stop_loss']

    df = get_klines(symbol, interval='5m', limit=STOP_LOOKBACK)
    if df.empty or len(df) < STOP_LOOKBACK:
        return

    decimals = get_price_decimals(symbol)

    if side == 'LONG':
        new_stop = df['low'].min()
        if old_stop is None or new_stop > old_stop:
            try:
                cancel_open_stop_orders(symbol)
                stop_price = round(new_stop * 0.999, decimals)
                client.futures_create_order(
                    symbol=symbol,
                    side='SELL',
                    type='STOP_MARKET',
                    stopPrice=str(stop_price),
                    closePosition=True,
                    timeInForce='GTC'
                )
                positions_state[symbol]['stop_loss'] = new_stop
                log(f"🔄 Stop LONG atualizado para {stop_price} em {symbol}")
                send_telegram(f"🔄 Stop LONG atualizado para {symbol}: {stop_price}")
                send_discord(f"🔄 Stop LONG atualizado para {symbol}: {stop_price}")
            except Exception as e:
                log(f"Erro ao atualizar stop LONG {symbol}: {e}")
    else:
        new_stop = df['high'].max()
        if old_stop is None or new_stop < old_stop:
            try:
                cancel_open_stop_orders(symbol)
                stop_price = round(new_stop * 1.001, decimals)
                client.futures_create_order(
                    symbol=symbol,
                    side='BUY',
                    type='STOP_MARKET',
                    stopPrice=str(stop_price),
                    closePosition=True,
                    timeInForce='GTC'
                )
                positions_state[symbol]['stop_loss'] = new_stop
                log(f"🔄 Stop SHORT atualizado para {stop_price} em {symbol}")
                send_telegram(f"🔄 Stop SHORT atualizado para {symbol}: {stop_price}")
                send_discord(f"🔄 Stop SHORT atualizado para {symbol}: {stop_price}")
            except Exception as e:
                log(f"Erro ao atualizar stop SHORT {symbol}: {e}")

def monitor_position(symbol):
    if symbol not in positions_state:
        return
    try:
        pos = client.futures_position_information(symbol=symbol)
        for p in pos:
            amt = float(p['positionAmt'])
            if amt == 0.0:
                if positions_state[symbol]['open']:
                    side = positions_state[symbol]['side']
                    qty = positions_state[symbol]['qty']
                    entry_price = float(p['entryPrice'])
                    exit_price = float(client.futures_symbol_ticker(symbol=symbol)['price'])
                    pnl = (exit_price - entry_price) * qty if side == 'LONG' else (entry_price - exit_price) * qty
                    pnl = round(pnl, 2)
                    percent = ((exit_price - entry_price) / entry_price * 100) if side == 'LONG' else ((entry_price - exit_price) / entry_price * 100)
                    percent = round(percent, 2)

                    msg = f"✅ Posição encerrada para {symbol}.\n💼 Resultado: {'lucro' if pnl > 0 else 'prejuízo'} de {pnl} USDT ({percent}%)"
                    log(msg)
                    send_telegram(msg)
                    send_discord(msg)

                positions_state[symbol]['open'] = False
                positions_state[symbol]['side'] = None
                positions_state[symbol]['stop_loss'] = None
                positions_state[symbol]['qty'] = 0.0
                cancel_all_open_orders(symbol)
    except Exception as e:
        log(f"Erro ao monitorar posição {symbol}: {e}")

def cancel_all_open_orders(symbol):
    try:
        open_orders = client.futures_get_open_orders(symbol=symbol)
        for order in open_orders:
            client.futures_cancel_order(symbol=symbol, orderId=order['orderId'])
            log(f"🗑️ Ordem cancelada para {symbol}: ID {order['orderId']}")
    except Exception as e:
        log(f"Erro ao cancelar ordens para {symbol}: {e}")

# ========== FLUXO PRINCIPAL DAS TAREFAS ==========
def task_check_signals():
    for symbol in SYMBOLS:
        if symbol not in positions_state:
            positions_state[symbol] = {'open': False, 'side': None, 'stop_loss': None, 'qty': 0.0}
        if positions_state[symbol]['open']:
            log(f"⚠️ Posição já aberta para {symbol}.")
            continue
        rsi_long, rsi_short = check_rsi_trigger(symbol)
        ma_signal = check_ma_crossover(symbol)

        direction = CONFIGS.get(symbol, {}).get('direction', 'BOTH')

        if ma_signal == 'LONG' and rsi_long and direction in ['LONG', 'BOTH']:
            log(f"🔔 Sinal COMPRA (LONG) detectado para {symbol}")
            place_order(symbol, 'LONG', get_usdt_balance() * CONFIGS[symbol]['risk_percent'])
        elif ma_signal == 'SHORT' and rsi_short and direction in ['SHORT', 'BOTH']:
            log(f"🔻 Sinal VENDA (SHORT) detectado para {symbol}")
            place_order(symbol, 'SHORT', get_usdt_balance() * CONFIGS[symbol]['risk_percent'])
        else:
            log(f"ℹ️ Nenhum sinal válido para {symbol} ou direção não permitida.")

def task_update_stop_loss():
    for symbol in SYMBOLS:
        update_stop_loss(symbol)

def task_monitor_positions():
    for symbol in SYMBOLS:
        monitor_position(symbol)

# ========== INICIALIZAÇÃO E LOOP ==========
def startup_checks():
    total_risk = 0.0
    usdt_balance = get_usdt_balance()
    usdt_available = get_available_margin()

    log("🚀 Bot iniciado")
    log(f"💰 Saldo total: {usdt_balance:.2f} USDT")
    log(f"📉 Margem disponível: {usdt_available:.2f} USDT")

    send_telegram(f"🚀 Bot ativo\n💰 Total: {usdt_balance:.2f}\n📉 Margem: {usdt_available:.2f}")
    send_discord(f"🚀 Bot ativo\n💰 Total: {usdt_balance:.2f}\n📉 Margem: {usdt_available:.2f}")

    for symbol in SYMBOLS:
        config = CONFIGS[symbol]
        risk = usdt_balance * config['risk_percent']
        total_risk += risk
        log(f"⚙️ {symbol}: Alavancagem {config['leverage']}x | Risco {config['risk_percent']*100:.1f}% = {risk:.2f} USDT")

    log(f"📈 Total potencial por operação: {total_risk:.2f} USDT")
    send_telegram(f"📈 Total potencial por operação: {total_risk:.2f} USDT")
    send_discord(f"📈 Total potencial por operação: {total_risk:.2f} USDT")

def detect_open_positions():
    # Detecta posições abertas e atualiza estado inicial
    try:
        for symbol in SYMBOLS:
            if symbol not in positions_state:
                positions_state[symbol] = {'open': False, 'side': None, 'stop_loss': None, 'qty': 0.0}
            positions = client.futures_position_information(symbol=symbol)
            for p in positions:
                amt = float(p['positionAmt'])
                if amt != 0.0:
                    side = 'LONG' if amt > 0 else 'SHORT'
                    qty = abs(amt)
                    entry_price = float(p['entryPrice'])
                    positions_state[symbol].update({
                        'open': True,
                        'side': side,
                        'qty': qty,
                        'stop_loss': None
                    })
                    log(f"🔄 Posição aberta detectada para {symbol}!")
                    log(f"📌 Tipo: {side} | Quantidade: {qty} | Entrada: {entry_price}")
                    send_telegram(f"🔄 Posição {side} detectada na inicialização para {symbol}\nQtd: {qty}\nEntrada: {entry_price}")
                    send_discord(f"🔄 Posição {side} detectada na inicialização para {symbol}\nQtd: {qty}\nEntrada: {entry_price}")
                break
    except Exception as e:
        log(f"Erro ao detectar posições abertas: {e}")

if __name__ == "__main__":
    # Executa checagens iniciais
    startup_checks()

    # Agenda as tarefas
    schedule.every(15).minutes.do(task_check_signals)
    schedule.every(5).minutes.do(task_update_stop_loss)
    schedule.every(60).seconds.do(task_monitor_positions)
    schedule.every(3).minutes.do(detect_open_positions)

    log("🟢 Iniciando loop principal...")
    while True:
        schedule.run_pending()
        time.sleep(1)
