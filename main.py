import os
import json
import time
import schedule
from dotenv import load_dotenv

from utils.core import (
    initialize_configs,
    detect_open_positions,
    place_order,
    update_stop_loss,
    monitor_position,
    cancel_all_open_orders,
    cancel_orders_if_no_position,
    get_klines,
    get_available_margin,
    rsi_trigger_flags,
    positions_state,
    get_usdt_balance,
    LEVERAGE,
    RISK_PERCENT,
    DECIMALS,
    send_telegram,
    log,
    get_available_margin
)

from utils.strategies import check_signals_scalper, check_signals_turtle

load_dotenv()

# Carrega configuração de moedas do .env
CONFIGS = json.loads(os.getenv("COIN_CONFIGS"))
initialize_configs(CONFIGS)

SYMBOLS = list(CONFIGS.keys())

def task_check_signals():
    for symbol in SYMBOLS:
        config = CONFIGS[symbol]
        strategy = config.get('strategy', 'scalper')  # padrão scalper

        if symbol not in positions_state:
            positions_state[symbol] = {'open': False, 'side': None, 'stop_loss': None, 'qty': 0.0}
        if symbol not in rsi_trigger_flags:
            rsi_trigger_flags[symbol] = {'LONG': False, 'SHORT': False}

        if positions_state[symbol]['open']:
            log(f"⚠️ Posição já aberta para {symbol}.")
            continue

        if strategy == 'scalper':
            check_signals_scalper(symbol)
        elif strategy == 'turtle':
            check_signals_turtle(symbol)


def task_update_stop_loss():
    for symbol in SYMBOLS:
        update_stop_loss(symbol)

def task_monitor_positions():
    for symbol in SYMBOLS:
        monitor_position(symbol)

def startup_checks():
    total_margin_used = 0.0
    total_position_usdt = 0.0
    usdt_balance = get_usdt_balance()
    usdt_available = get_available_margin()

    log("🚀 Bot iniciado")
    log(f"💰 Saldo total: {usdt_balance:.2f} USDT")
    log(f"📉 Margem disponível: {usdt_available:.2f} USDT")

    send_telegram(f"🚀 Bot ativo\n💰 Total: {usdt_balance:.2f}\n📉 Margem: {usdt_available:.2f}")

    log("📋 Moedas em operação:")

    for symbol in SYMBOLS:
        config = CONFIGS[symbol]
        leverage = config.get("leverage", LEVERAGE)
        risk_percent = config.get("risk_percent", RISK_PERCENT)
        strategy = config.get("strategy", "scalper")
        direction = config.get("direction", "BOTH")

        take_profit_percent = config.get("take_profit_percent", 0.0) * 100  # converter para %

        margin_used = usdt_available * risk_percent
        position_usdt = margin_used * leverage

        total_margin_used += margin_used
        total_position_usdt += position_usdt

        # Monta mensagem diferente se for turtle
        if strategy == "turtle":
            msg = (
                f"➡️ {symbol} | Estratégia: {strategy} | Direção: {direction} | "
                f"Alav: {leverage}x | "
                f"Margem usada: {margin_used:.2f} USDT | Posição estimada: {position_usdt:.2f} USDT"
            )
        else:
            msg = (
                f"➡️ {symbol} | Estratégia: {strategy} | Direção: {direction} | "
                f"Alav: {leverage}x | TP: {take_profit_percent:.2f}% | "
                f"Margem usada: {margin_used:.2f} USDT | Posição estimada: {position_usdt:.2f} USDT"
            )

        log(msg)
        send_telegram(msg)

    margin_msg = f"📊 Total margem usada: {total_margin_used:.2f} USDT"
    position_msg = f"📈 Total estimado em posições alavancadas: {total_position_usdt:.2f} USDT"

    log(margin_msg)
    log(position_msg)
    send_telegram(margin_msg)
    send_telegram(position_msg)



if __name__ == "__main__":
    startup_checks()

    # Detectar posições abertas no startup
    detect_open_positions()

    # Agenda as tarefas periódicas
    schedule.every(3).minutes.do(task_check_signals)
    schedule.every(5).minutes.do(task_update_stop_loss)
    schedule.every(60).seconds.do(task_monitor_positions)
    schedule.every(5).minutes.do(detect_open_positions)
    schedule.every(1).minutes.do(cancel_orders_if_no_position)

    log("🟢 Iniciando loop principal...")
    while True:
        schedule.run_pending()
        time.sleep(1)
