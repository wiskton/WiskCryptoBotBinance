# WiskCryptoBotBinance

# 📈 Bot de Trade Automatizado - Binance Futuros

Este bot realiza operações automáticas de **long/short** no mercado **Futures da Binance** com base em sinais técnicos (RSI + cruzamento de MAs), gerenciamento de risco por par e envio de alertas para **Telegram e Discord**.

---

## ⚙️ Funcionalidades

- Estratégia com **RSI + MA crossover**
- Controle de risco por ativo (alavancagem e % de risco configurável)
- Suporte a múltiplos pares simultaneamente
- Notificações automáticas para Telegram e Discord
- Atualização dinâmica de Stop Loss
- Detecta posições já abertas ao iniciar
- Cancelamento automático de ordens pendentes

---

## 📁 Estrutura de Pastas

```
project/
├── main.py
├── setup_bot.sh
├── requirements.txt
├── .env
├── utils/
│   ├── telegram.py
│   ├── discord.py
│   └── util.py
```

---

## ✅ Pré-requisitos

- Conta na Binance habilitada para **Futures**
- Python 3.9+
- Linux ou WSL recomendado
- Pacotes do sistema:
  ```bash
  sudo apt install python3-venv python3-pip -y
  ```

---

## 🚀 Passo a passo para rodar o bot

### 1. Clone o repositório

```bash
git clone https://github.com/wiskton/WiskCryptoBotBinance
cd WiskCryptoBotBinance
```

### 2. Execute o script de setup

```bash
chmod +x setup_bot.sh
./setup_bot.sh
```

O script irá:

- Criar um ambiente virtual Python (`venv/`)
- Instalar as dependências (`ta`, `python-binance`, `pandas`, etc.)
- Criar o arquivo `.env` com as variáveis de API
- Executar o bot automaticamente

---

## 🔐 Configuração do `.env`

Preencha com suas credenciais:

```
BINANCE_API_KEY=sua_chave_api
BINANCE_API_SECRET=sua_chave_secreta
TELEGRAM_BOT_TOKEN=seu_token_bot_telegram
TELEGRAM_CHAT_ID=seu_chat_id
DISCORD_WEBHOOK_URL=sua_webhook_discord
COIN_CONFIGS={"BTCUSDT":{"leverage":20,"risk_percent":0.05,"direction":"BOTH","take_profit_percent":0.015},"ETHUSDT":{"leverage":10,"risk_percent":0.05,"direction":"BOTH","take_profit_percent":0.015},"PENDLEUSDT":{"leverage":10,"risk_percent":0.05,"direction":"BOTH","take_profit_percent":0.02},"VIRTUALUSDT":{"leverage":10,"risk_percent":0.05,"direction":"BOTH","take_profit_percent":0.02},"1000PEPEUSDT":{"leverage":5,"risk_percent":0.05,"direction":"BOTH","take_profit_percent":0.025},"WIFUSDT":{"leverage":5,"risk_percent":0.05,"direction":"BOTH","take_profit_percent":0.025},"PNUTUSDT":{"leverage":5,"risk_percent":0.05,"direction":"SHORT","take_profit_percent":0.025}}
```

---

## ⚙️ Configuração dos pares

Dentro do `main.py`, edite o dicionário `CONFIGS` para definir os pares e seus parâmetros:

```python
CONFIGS = {
    'BTCUSDT': {'leverage': 20, 'risk_percent': 0.05, 'direction': 'LONG'},
    'ETHUSDT': {'leverage': 10, 'risk_percent': 0.05, 'direction': 'LONG'},
    'SOLUSDT': {'leverage': 5, 'risk_percent': 0.05, 'direction': 'BOTH'},
    ...
}
```

- `leverage`: Alavancagem usada para o par
- `risk_percent`: Percentual do saldo da conta usado por operação
- `direction`: `'LONG'`, `'SHORT'` ou `'BOTH'` (permitido)

---

## 📦 Dependências (caso precise instalar manualmente)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 📊 Logs e alertas

- Os logs são exibidos no terminal.
- As notificações são enviadas para **Telegram** e **Discord** com:
  - Posição aberta (tipo, preço, stop)
  - Stop atualizado
  - Posição encerrada com lucro/prejuízo

---

## ⏱️ Tarefas agendadas

- Checagem de sinais: a cada 3 minutos
- Atualização do stop loss: a cada 5 minutos
- Verificação de encerramento de posição: a cada 60 segundos
- Detecção de posições abertas: a cada 3 minutos

---

## 🛑 Encerrar o bot

Pressione `Ctrl + C` para parar a execução.
