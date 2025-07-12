#!/bin/bash

echo "🔧 Iniciando configuração do bot..."

# Criação de ambiente virtual se não existir
if [ ! -d "venv" ]; then
  echo "📁 Criando ambiente virtual Python..."
  python3 -m venv venv
fi

# Verifica se o pip foi criado corretamente
if [ ! -f "venv/bin/pip" ]; then
  echo "❌ Erro: o pip não foi criado no ambiente virtual."
  echo "👉 Tente instalar com: sudo apt install python3-venv python3-pip -y"
  exit 1
fi

# Criação do .env se não existir
if [ ! -f ".env" ]; then
  echo "📄 Criando arquivo .env..."
  cat <<EOF > .env
BINANCE_API_KEY=SUA_API_KEY
BINANCE_API_SECRET=SUA_API_SECRET
TELEGRAM_BOT_TOKEN=SEU_BOT_TOKEN
TELEGRAM_CHAT_ID=SEU_CHAT_ID
EOF
  echo "⚠️ Arquivo .env criado. Edite-o e insira suas credenciais antes de executar o bot."
fi

# Instalação de dependências usando pip do ambiente virtual
echo "📦 Instalando dependências no ambiente virtual..."
venv/bin/pip install --upgrade pip
venv/bin/pip install -r requirements.txt

# Executa o bot diretamente (sem argumentos)
echo "🚀 Iniciando o bot..."
venv/bin/python main.py
