# 📊 OCI FinOps Analyzer — CPU, Memory & Burstable Baseline

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
![OCI](https://img.shields.io/badge/Cloud-Oracle_Cloud_Infrastructure-orange)
![FinOps](https://img.shields.io/badge/Focus-FinOps-blueviolet)
![Automation](https://img.shields.io/badge/Automation-Yes-success)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Ferramenta profissional desenvolvida para **analisar o uso real de CPU, Memória e Baseline Burstable** de todas as instâncias OCI Compute, gerando insights e recomendações **FinOps** automáticas.

Desenvolvido e mantido por **Bruno Mendes Augusto**  
BS4IT — Cloud AWS | OCI | DevOps | FinOps  
GitHub: https://github.com/bruno0nline

---

# ✨ Funcionalidades

- 🔍 Varredura automática de **todas as regiões OCI**
- 🗂 Coleta em **todos os compartments**, incluindo filhos
- 📊 Análise histórica de **N dias** (padrão: 30)
- 📈 Cálculo de:
  - Média (Mean) de CPU e Memória  
  - Percentil 95 (P95) de CPU e Memória  
- 🔥 Detecção precisa de:
  - Instâncias **burstable**
  - Baseline configurada: **12.5%**, **50%**, ou **desativada**
- 🤖 Recomendações automáticas FinOps:
  - 🟩 **KEEP**
  - 🟥 **DOWNSIZE**, **DOWNSIZE-STRONG**, **DOWNSIZE-MEM**
  - 🟨 **UPSCALE**
  - 🔵 **BURSTABLE SUGGESTED** (12.5% ou 50%)
- 📤 Exportação automática para:
  - **CSV**
  - **Excel (.xlsx)** com cores (verde/amarelo/vermelho)
  - **Word (.docx)** com relatório executivo para gestores
- ☁️ Execução 100% compatível com **OCI Cloud Shell** (recomendado)

---

# 📁 Estrutura do Projeto

```text
oci-metrics-cpu-mem-report/
├── src/
│   ├── oci_metrics_cpu_mem_media_ndays.py        # Script principal FinOps
│   ├── oci_metrics_cpu_mem_realtime.py           # Coleta rápida (últimos 30 min)
│   └── oci_metrics_cpu_mem_word_report.py        # Relatório DOCX para gestão
│
├── docs/
│   ├── README_WIKI.md                            # Documentação interna para equipes
│   └── PRESENTACAO_GESTAO.md                     # Resumo executivo FinOps
│
├── examples/
│   ├── sample_output.csv
│   ├── sample_output.xlsx
│   └── sample_word_report.docx
│
├── requirements.txt
└── README.md
🚀 Como usar
1. Clonar o repositório
bash
Copiar código
git clone https://github.com/bruno0nline/oci-metrics-cpu-mem-report.git
cd oci-metrics-cpu-mem-report
2. Criar e ativar ambiente virtual
bash
Copiar código
python3 -m venv .venv
source .venv/bin/activate
3. Instalar dependências
bash
Copiar código
pip install -r requirements.txt
4. Definir período de análise
Exemplo: analisar os últimos 30 dias

bash
Copiar código
export METRICS_DAYS=30
5. Executar o relatório principal FinOps
bash
Copiar código
python3 src/oci_metrics_cpu_mem_media_ndays.py
Arquivos gerados na home do usuário:

perl
Copiar código
~/Relatorio_CPU_Memoria_media_30d_multi_region.csv
~/Relatorio_CPU_Memoria_media_30d_multi_region.xlsx
6. Gerar relatório executivo em Word
bash
Copiar código
python3 src/oci_metrics_cpu_mem_word_report.py
Saída:

Copiar código
~/Relatorio_FinOps_CPU_Mem_30d_multi_region.docx
📊 Exemplo de Recomendações
Instância	CPU Mean	Mem Mean	Burstable	Recomendação
vm-app01	9%	22%	NO	🟥 DOWNSIZE
vm-db02	65%	88%	NO	🟨 UPSCALE
vm-web03	30%	41%	12.5%	🟩 KEEP
vm-scan	4%	18%	NO	🔵 BURSTABLE-12.5%

🔧 Scripts Disponíveis
oci_metrics_cpu_mem_media_ndays.py
Coleta completa multi-região, avalia tendências, calcula médias e p95, identifica baseline burstable e gera CSV/XLSX.

oci_metrics_cpu_mem_realtime.py
Consulta rápida das últimas métricas (últimos 30 minutos).

oci_metrics_cpu_mem_word_report.py
Gera documento Word com recomendações FinOps, pronto para enviar a gestores.

🤝 Contribuições
Pull requests são bem-vindos!
Sugestões podem ser enviadas na aba Issues do repositório.

📜 Licença
Distribuído sob a licença MIT.

