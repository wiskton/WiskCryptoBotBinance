# WiskCryptoBotBinance

Bot de trading automático para Binance Futuros, implementando estratégias Scalper e Turtle, com controle de alavancagem, risco, direções e take profit por moeda.

---

## Recursos

- Suporte a múltiplas moedas configuráveis via variável de ambiente `COIN_CONFIGS`
- Estratégias Scalper e Turtle selecionáveis por moeda
- Gestão de posições com stop loss dinâmico baseado em candles recentes
- Abertura e fechamento de posições com ordens de mercado, stop loss e take profit
- Logs e notificações via Telegram
- Atualização automática de stops e monitoramento das posições
- Modularização do código para facilitar manutenção

---

## Instalação

1. Clone o repositório:

```bash
git clone https://github.com/wiskton/WiskCryptoBotBinance.git
cd WiskCryptoBotBinance
```

2. Crie e ative um ambiente virtual (opcional mas recomendado):

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

3. Instale as dependências:

```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto com:

```env
BINANCE_API_KEY=suas_chaves_aqui
BINANCE_API_SECRET=suas_chaves_aqui
TELEGRAM_BOT_TOKEN=seu_token_telegram
TELEGRAM_CHAT_ID=seu_chat_id
COIN_CONFIGS={"ETHUSDT":{"leverage":10,"risk_percent":0.1,"direction":"LONG","take_profit_percent":0.015,"strategy":"turtle"},"XRPUSDT":{"leverage":10,"risk_percent":0.1,"direction":"LONG","take_profit_percent":0.015,"strategy":"turtle"},"BRETTUSDT":{"leverage":5,"risk_percent":0.1,"direction":"BOTH","take_profit_percent":0.015,"strategy":"turtle"},"PONKEUSDT":{"leverage":5,"risk_percent":0.1,"direction":"BOTH","take_profit_percent":0.015,"strategy":"turtle"},"1000PEPEUSDT":{"leverage":5,"risk_percent":0.1,"direction":"BOTH","take_profit_percent":0.015,"strategy":"turtle"},"VIRTUALUSDT":{"leverage":5,"risk_percent":0.1,"direction":"LONG","take_profit_percent":0.015,"strategy":"turtle"},"PNUTUSDT":{"leverage":5,"risk_percent":0.1,"direction":"SHORT","take_profit_percent":0.02,"strategy":"scalper"},"HMSTRUSDT":{"leverage":5,"risk_percent":0.1,"direction":"SHORT","take_profit_percent":0.02,"strategy":"scalper"}}

```

*Adapte `COIN_CONFIGS` conforme suas moedas e preferências.*

---

## Configuração `COIN_CONFIGS`

Configuração JSON para cada moeda:

| Par       | leverage | risk_percent | direction | take_profit_percent | strategy  |
|-----------|----------|--------------|-----------|---------------------|-----------|
| BTCUSDT   | 20       | 0.05         | BOTH      | 0.015               | scalper   |
| ETHUSDT   | 10       | 0.05         | BOTH      | 0.015               | scalper   |

- `leverage`: alavancagem para a moeda
- `risk_percent`: percentual do saldo usado para o tamanho da posição
- `direction`: `LONG`, `SHORT` ou `BOTH`
- `take_profit_percent`: percentual para take profit
- `strategy`: `scalper` ou `turtle`

---

## Uso

Execute o bot com:

```bash
python main.py
```

O bot fará:

- Checagem inicial e reporta saldo e configurações via Telegram
- Periodicamente verifica sinais e abre posições conforme a estratégia da moeda
- Atualiza stops e monitora posições abertas
- Cancela ordens caso não haja posição aberta
- Envia logs detalhados

---

## Estrutura do projeto

```
WiskCryptoBotBinance/
├── main.py            # Script principal com loop e agendamento
├── requirements.txt   # Dependências Python
├── .env               # Variáveis de ambiente (não versionar)
├── utils/
│   ├── core.py        # Funções de lógica, indicadores e operações
│   ├── telegram.py    # Envio de mensagens Telegram
│   ├── strategy.py    # Funções de estratégias
│   └── util.py        # Função de log e utilitários gerais
└── README.md
```

---

## Dependências

- python-binance
- pandas
- ta (Technical Analysis Library)
- python-dotenv
- schedule
- requests (para Telegram)

Instale com:

```bash
pip install -r requirements.txt
```

---

## Contato

Dúvidas e sugestões? Abra uma issue no GitHub ou envie mensagem.

---

## Aviso

Este bot é para uso educativo. Riscos financeiros envolvem perda de capital. Use com responsabilidade.

---

**WiskCryptoBotBinance © 2025**
