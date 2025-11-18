cat > README.md <<'EOF'
# OCI Metrics CPU & Memory Report

Projeto em Python para coletar métricas de **CPU** e **Memória** das instâncias de Compute na Oracle Cloud Infrastructure (OCI), usando o **Monitoring API**.

O objetivo é apoiar análises de **FinOps**, mostrando a média de uso de CPU e memória em um período configurável (ex.: 30 dias), ajudando a identificar oportunidades de **downsizing** ou **upsizing** de máquinas.

## Estrutura

- `src/oci_metrics_cpu_mem_media_ndays.py`  
  Coleta a média de CPU e Memória das instâncias em RUNNING nos últimos **N dias** (padrão: 30) e gera um CSV.

- `requirements.txt`  
  Dependências do projeto.

## Pré-requisitos

- Conta na OCI com permissões de leitura em:
  - Métricas (`oci_computeagent`)
  - Instâncias (`instance-family`)
- Python 3 (no Cloud Shell já vem pronto).
- Arquivo de configuração `~/.oci/config` válido (Cloud Shell já usa o do usuário logado).

## Uso rápido no Cloud Shell

```bash
# 1) Clonar o repositório
git clone https://github.com/bruno0nline/oci-metrics-cpu-mem-report.git
cd oci-metrics-cpu-mem-report

# 2) Criar e ativar o ambiente virtual (opcional, mas recomendado)
python3 -m venv .venv
source .venv/bin/activate

# 3) Instalar dependências
pip install -r requirements.txt

# 4) Definir janela de análise (em dias)
export METRICS_DAYS=30   # exemplo: 30 dias

# 5) Executar o script
python3 src/oci_metrics_cpu_mem_media_ndays.py


Saída esperada no terminal (exemplo):

Coletando médias de CPU/Mem dos últimos 30 dias...
Total de instâncias em RUNNING: 4

[1/4] APP-SRV01:
  - CPU média   : 12.34 %
  - Mem média   : 45.67 %

[2/4] DB-SRV01:
  - CPU média   : 3.21 %
  - Mem média   : 78.90 %

✅ Relatório gerado: Relatorio_CPU_Memoria_media_30d.csv
