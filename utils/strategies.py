import ta
from utils.core import (
    get_klines,
    log,
    place_order,
    get_available_margin,
    rsi_trigger_flags,
    RISK_PERCENT,
    CONFIGS,
)

def update_rsi_trigger(symbol, interval='1h'):
    df = get_klines(symbol, interval=interval, limit=100)
    if df.empty:
        return
    df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
    last_rsi = df['rsi'].iloc[-1]

    if last_rsi <= 30:
        rsi_trigger_flags[symbol]['LONG'] = True
        log(f"{symbol} RSI LONG trigger ativado (RSI={last_rsi:.2f})")
    elif last_rsi >= 70:
        rsi_trigger_flags[symbol]['SHORT'] = True
        log(f"{symbol} RSI SHORT trigger ativado (RSI={last_rsi:.2f})")

def check_signals_scalper(symbol):
    # Etapa 1: Atualiza trigger RSI (1h)
    update_rsi_trigger(symbol)

    # Etapa 2: Verifica cruzamento de MAs no 3m
    df = get_klines(symbol, interval='3m', limit=100)
    if df.empty or len(df) < 22:
        log(f"⛔ Dados insuficientes para médias móveis {symbol}")
        return

    df['ma9'] = df['close'].rolling(window=9).mean()
    df['ma21'] = df['close'].rolling(window=21).mean()

    ma9_prev, ma9_curr = df['ma9'].iloc[-2], df['ma9'].iloc[-1]
    ma21_prev, ma21_curr = df['ma21'].iloc[-2], df['ma21'].iloc[-1]

    direction = CONFIGS.get(symbol, {}).get('direction', 'BOTH')
    risk_percent = CONFIGS.get(symbol, {}).get('risk_percent', RISK_PERCENT)

    # Compra: cruzamento de alta + trigger RSI LONG
    if ma9_prev < ma21_prev and ma9_curr > ma21_curr and rsi_trigger_flags[symbol].get('LONG') and direction in ['LONG', 'BOTH']:
        log(f"🔔 Sinal COMPRA (LONG) confirmado para {symbol} (RSI + MA9>MA21)")
        if place_order(symbol, 'LONG', get_available_margin() * risk_percent):
            rsi_trigger_flags[symbol]['LONG'] = False

    # Venda: cruzamento de baixa + trigger RSI SHORT
    elif ma9_prev > ma21_prev and ma9_curr < ma21_curr and rsi_trigger_flags[symbol].get('SHORT') and direction in ['SHORT', 'BOTH']:
        log(f"🔻 Sinal VENDA (SHORT) confirmado para {symbol} (RSI + MA9<MA21)")
        if place_order(symbol, 'SHORT', get_available_margin() * risk_percent):
            rsi_trigger_flags[symbol]['SHORT'] = False

    else:
        log(f"ℹ️ {symbol} sem sinal (RSI ou MA cruzamento não confirmados)")

def check_signals_turtle(symbol):
    # Etapa 1: Verifica RSI (1h) e atualiza flag
    update_rsi_trigger(symbol)

    # Etapa 2: Verifica rompimento dos últimos 20 candles no 1h
    df = get_klines(symbol, interval='1h', limit=21)
    if df.empty or len(df) < 21:
        return

    breakout_high = df['high'][:-1].max()
    breakout_low = df['low'][:-1].min()
    last_close = df['close'].iloc[-1]

    direction = CONFIGS.get(symbol, {}).get('direction', 'BOTH')
    risk_percent = CONFIGS.get(symbol, {}).get('risk_percent', RISK_PERCENT)

    if last_close > breakout_high and rsi_trigger_flags[symbol]['LONG'] and direction in ['LONG', 'BOTH']:
        log(f"🐢 Turtle LONG breakout confirmado para {symbol}")
        success = place_order(symbol, 'LONG', get_available_margin() * risk_percent)
        if success:
            rsi_trigger_flags[symbol]['LONG'] = False

    elif last_close < breakout_low and rsi_trigger_flags[symbol]['SHORT'] and direction in ['SHORT', 'BOTH']:
        log(f"🐢 Turtle SHORT breakout confirmado para {symbol}")
        success = place_order(symbol, 'SHORT', get_available_margin() * risk_percent)
        if success:
            rsi_trigger_flags[symbol]['SHORT'] = False
