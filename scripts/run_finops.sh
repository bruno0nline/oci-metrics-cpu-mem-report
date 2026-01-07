#!/bin/bash

set -e

echo "🔍 OCI FinOps Analyzer - Execução automática"
echo "👤 Autor: Bruno Mendes Augusto"
echo "--------------------------------------------"

# Caminho base do projeto
BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"

cd "$BASE_DIR"

# Criar venv se não existir
if [ ! -d ".venv" ]; then
  echo "📦 Criando ambiente virtual..."
  python3 -m venv .venv
fi

# Ativar venv
source .venv/bin/activate

echo "📥 Instalando dependências..."
pip install --upgrade pip >/dev/null
pip install -r requirements.txt >/dev/null

echo "📊 Gerando CSV e XLSX (relatório principal)..."
python3 src/oci_metrics_cpu_mem_media_ndays.py

echo "📄 Gerando relatório Word técnico (todas as recomendações)..."
python3 src/oci_metrics_cpu_mem_word_technical.py

echo "🏆 Gerando relatório Word Top 5 impacto financeiro..."
python3 src/oci_metrics_cpu_mem_word_top5.py

echo "--------------------------------------------"
echo "✅ Execução finalizada com sucesso!"
echo ""
echo "📂 Arquivos gerados na HOME do usuário:"
echo " - CSV + XLSX (relatório completo)"
echo " - DOCX técnico (todas recomendações)"
echo " - DOCX Top 5 impacto financeiro"
