# 🐢 WiskCryptoBotBinance

Bot de trading automatizado para Binance Futures usando a estratégia **Turtle + RSI + Cruzamento de Médias Móveis**, com controle de risco e notificações via Telegram e Discord.

📍 Repositório: [github.com/wiskton/WiskCryptoBotBinance](https://github.com/wiskton/WiskCryptoBotBinance/)

---

## ⚙️ Funcionalidades

- Estratégia combinada: **RSI + MA crossover + Turtle Stop**
- Suporte a múltimos pares simultaneamente
- Compatível com **Binance Futures**
- Gerenciamento de risco individual por ativo
- Configuração de:
  - Alavancagem
  - Percentual de risco
  - Direção de operação (`LONG`, `SHORT` ou `BOTH`)
  - Percentual de **take profit**
- Atualização automática do stop loss
- Detecção de posições abertas
- Cancelamento de ordens pendentes
- Notificações via **Telegram** e **Discord**
- Modular e escalável

---

## 🧠 Estratégia

1. **RSI (1h)**:
   - LONG se RSI ≤ 30
   - SHORT se RSI ≥ 70
2. **Cruzamento de MAs (3m)**:
   - MA9 cruza MA21 de baixo pra cima → LONG
   - MA9 cruza MA21 de cima pra baixo → SHORT
3. **Stop Loss dinâmico** com base no gráfico de 3m ou 5m
4. **Take Profit** por ativo configurável (ex: 1.5%, 2%, 2.5%)

---

## 📝 Requisitos

- Python 3.9+
- Conta na Binance Futures com API habilitada
- Conta no Telegram e/ou Discord (para alertas)

---

## 🚀 Instalação

```bash
git clone https://github.com/wiskton/WiskCryptoBotBinance.git
cd WiskCryptoBotBinance
pip install -r requirements.txt
```

---

## 🔐 Configuração

Crie um arquivo `.env` na raiz com o seguinte conteúdo:

```env
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_api_secret

TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id

DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

COIN_CONFIGS={"BTCUSDT":{"leverage":20,"risk_percent":0.05,"direction":"BOTH","take_profit_percent":0.015},"ETHUSDT":{"leverage":10,"risk_percent":0.05,"direction":"BOTH","take_profit_percent":0.015},"PENDLEUSDT":{"leverage":10,"risk_percent":0.05,"direction":"BOTH","take_profit_percent":0.02},"VIRTUALUSDT":{"leverage":10,"risk_percent":0.05,"direction":"BOTH","take_profit_percent":0.02},"1000PEPEUSDT":{"leverage":5,"risk_percent":0.05,"direction":"BOTH","take_profit_percent":0.025},"WIFUSDT":{"leverage":5,"risk_percent":0.05,"direction":"BOTH","take_profit_percent":0.025},"PNUTUSDT":{"leverage":5,"risk_percent":0.05,"direction":"SHORT","take_profit_percent":0.025}}
```

> 🧠 Use sempre aspas duplas e a configuração toda em uma única linha no `.env`

---

## ▶️ Executando o bot

```bash
python main.py
```

> O bot executa ciclos automaticamente a cada 3 minutos para sinais, 5 minutos para atualizar stop e 60 segundos para monitoramento.

---

## 📦 Estrutura do projeto

```
WiskCryptoBotBinance/
├── main.py               # Arquivo principal do bot
├── .env                  # Suas credenciais e configurações
├── requirements.txt      # Dependências
└── utils/
    ├── telegram.py       # Notificações no Telegram
    ├── discord.py        # Notificações no Discord
    └── util.py           # Funções auxiliares (logs, etc.)
```

---

## 🛡️ Aviso Legal

> ⚠️ **Este projeto é apenas para fins educacionais.** Trading de criptomoedas envolve risco. Use por sua conta e risco.

---

## 🙌 Contribuições

Sinta-se à vontade para abrir issues ou PRs com sugestões e melhorias.

---

## 📫 Contato

[https://github.com/wiskton](https://github.com/wiskton)
