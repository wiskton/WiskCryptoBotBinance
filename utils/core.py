import os
import math
import pandas as pd
from binance.client import Client
from utils.telegram import send_telegram
from utils.util import log

# Variáveis globais (serão inicializadas por initialize_configs)
CONFIGS = {}
positions_state = {}
rsi_trigger_flags = {}

API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

STOP_LOOKBACK = 20  # candle lookback para stop loss
LEVERAGE = 10       # alavancagem padrão
RISK_PERCENT = 0.05 # risco padrão 5%
DECIMALS = 3        # casas decimais para quantidade, ajustar conforme símbolo
STRATEGY = 'BOTH'
TAKE_PROFIT = 0.015

client = None  # será inicializado em initialize_configs

def initialize_configs(configs):
    global CONFIGS, positions_state, rsi_trigger_flags, client
    CONFIGS = configs
    positions_state.clear()
    rsi_trigger_flags.clear()
    for symbol in CONFIGS.keys():
        positions_state[symbol] = {'open': False, 'side': None, 'stop_loss': None, 'qty': 0.0}
        rsi_trigger_flags[symbol] = {'LONG': False, 'SHORT': False}
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
        return 0.001
    for filt in info['filters']:
        if filt['filterType'] == 'LOT_SIZE':
            return float(filt['minQty'])
    return 0.001

def round_qty(qty, symbol):
    min_qty = get_min_qty(symbol)
    qty = max(qty, min_qty)
    qty = round(qty, DECIMALS)
    remainder = qty % min_qty
    if remainder != 0:
        qty = qty - remainder
        if qty < min_qty:
            qty = min_qty
    return qty

def get_price_decimals(symbol):
    info = get_symbol_info(symbol)
    if not info:
        return 2
    for filt in info['filters']:
        if filt['filterType'] == 'PRICE_FILTER':
            tick_size = float(filt['tickSize'])
            decimals = abs(int(round(math.log10(tick_size))))
            return decimals
    return 2

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

    df = get_klines(symbol, interval='3m', limit=STOP_LOOKBACK)
    if df.empty or len(df) < STOP_LOOKBACK:
        log(f"Dados insuficientes para stop loss {symbol}")
        return False

    stop_loss_price = df['low'].min() if side == 'LONG' else df['high'].max()

    margin_available = get_available_margin()
    risk_percent = CONFIGS[symbol]['risk_percent']
    leverage = CONFIGS[symbol]['leverage']
    position_usdt = margin_available * risk_percent * leverage

    qty = round_qty(position_usdt / entry_price, symbol)
    if qty <= 0:
        log(f"Quantidade calculada inválida para {symbol}: {qty}")
        return False

    try:
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

    stop_price = round(stop_loss_price * (0.999 if side == 'LONG' else 1.001), 2)

    try:
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

    strategy = CONFIGS.get(symbol, {}).get('strategy', STRATEGY)
    if strategy != 'turtle':
        tp_percent = CONFIGS.get(symbol, {}).get('take_profit_percent', TAKE_PROFIT)
        if side == 'LONG':
            take_profit_price = round(entry_price * (1 + tp_percent), get_price_decimals(symbol))
        else:
            take_profit_price = round(entry_price * (1 - tp_percent), get_price_decimals(symbol))

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

    positions_state[symbol] = {
        'open': True,
        'side': side,
        'stop_loss': stop_loss_price,
        'qty': qty,
    }

    if strategy == 'turtle':
        log(f"🟢 {symbol} {side} aberto | Entrada: {entry_price} | Qtd: {qty} | SL: {stop_price}")
        send_telegram(f"🚀 {symbol} {side} aberto em {entry_price}\nSL: {stop_price}")
    else:
        log(f"🟢 {symbol} {side} aberto | Entrada: {entry_price} | Qtd: {qty} | SL: {stop_price} | TP: {take_profit_price}")
        send_telegram(f"🚀 {symbol} {side} aberto em {entry_price}\nSL: {stop_price} | TP: {take_profit_price}")



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

def cancel_all_open_orders(symbol):
    try:
        open_orders = client.futures_get_open_orders(symbol=symbol)
        for order in open_orders:
            client.futures_cancel_order(symbol=symbol, orderId=order['orderId'])
            log(f"🗑️ Ordem cancelada para {symbol}: ID {order['orderId']}")
    except Exception as e:
        log(f"Erro ao cancelar ordens para {symbol}: {e}")

def cancel_orders_if_no_position():
    for symbol in CONFIGS.keys():
        if not positions_state.get(symbol, {}).get('open', False):
            cancel_all_open_orders(symbol)

def update_stop_loss(symbol):
    if symbol not in positions_state or not positions_state[symbol]['open']:
        return

    config = CONFIGS[symbol]
    strategy = config.get("strategy", "scalper")
    side = positions_state[symbol]['side']
    old_stop = positions_state[symbol]['stop_loss']
    decimals = get_price_decimals(symbol)

    # Estratégia Turtle → usa gráfico de 1h e 20 candles
    if strategy == "turtle":
        interval = '1h'
        lookback = STOP_LOOKBACK
    else:
        interval = '5m'
        lookback = STOP_LOOKBACK  # Ex: 21 ou 30, já definido no topo do arquivo

    df = get_klines(symbol, interval=interval, limit=lookback)
    if df.empty or len(df) < lookback:
        return

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
                log(f"🔄 Stop LONG atualizado ({strategy}) para {stop_price} em {symbol}")
            except Exception as e:
                log(f"Erro ao atualizar stop LONG {symbol}: {e}")
    elif side == 'SHORT':
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
                log(f"🔄 Stop SHORT atualizado ({strategy}) para {stop_price} em {symbol}")
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

                positions_state[symbol]['open'] = False
                positions_state[symbol]['side'] = None
                positions_state[symbol]['stop_loss'] = None
                positions_state[symbol]['qty'] = 0.0
                cancel_all_open_orders(symbol)
    except Exception as e:
        log(f"Erro ao monitorar posição {symbol}: {e}")

def detect_open_positions():
    try:
        for symbol in CONFIGS.keys():
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
                break
    except Exception as e:
        log(f"Erro ao detectar posições abertas: {e}")
