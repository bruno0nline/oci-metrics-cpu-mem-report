
# 📊 OCI FinOps Analyzer — CPU & Memory

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
![OCI](https://img.shields.io/badge/Cloud-Oracle_Cloud_Infrastructure-orange)
![FinOps](https://img.shields.io/badge/Focus-FinOps-blueviolet)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Ferramenta **open-source**, simples e poderosa, para analisar o uso de **CPU** e **Memória** das instâncias OCI Compute e gerar recomendações automáticas de **FinOps** para redução de custos ou ajuste de capacidade.

Desenvolvido e mantido por **Bruno Mendes Augusto**.

---

## ✨ Funcionalidades

- 🔍 Varredura automática de **todas as regiões** da tenancy
- 🗂 Suporte a **todos os compartments** (raiz + filhos)
- ⏱ Análise histórica dos últimos **N dias** (padrão: 30)
- 📈 Cálculo de:
  - Média de CPU / Memória
  - Percentil 95 (P95) de CPU / Memória
- 🤖 Recomendações automáticas FinOps:
  - 🟩 `KEEP`
  - 🟥 `DOWNSIZE`, `DOWNSIZE-STRONG`, `DOWNSIZE-MEM`
  - 🟨 `UPSCALE`
- 📤 Geração automática de:
  - Arquivo **CSV** detalhado
  - Planilha **Excel (.xlsx)** com cores por recomendação (verde, amarelo, vermelho)
- ☁️ Totalmente compatível com **OCI Cloud Shell**

---

## 📁 Estrutura do Projeto

```text
oci-metrics-cpu-mem-report/
├── src/
│   ├── oci_metrics_cpu_mem_media_ndays.py   # Script principal FinOps
│   └── oci_metrics_cpu_mem_realtime.py      # Relatório rápido (30 min)
├── docs/
│   ├── README_WIKI.md                       # Documentação interna (wiki)
│   └── PRESENTACAO_GESTAO.md                # Visão executiva para gestão
├── examples/
│   ├── sample_output.csv
│   └── sample_output.xlsx
├── requirements.txt
└── README.md
```

---

## 🚀 Como usar

### 1. Clonar o repositório

```bash
git clone https://github.com/bruno0nline/oci-metrics-cpu-mem-report.git
cd oci-metrics-cpu-mem-report
```

### 2. Criar e ativar ambiente virtual

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar dependências

```bash
pip install -r requirements.txt
```

### 4. Definir período de análise (em dias)

Exemplo: 30 dias

```bash
export METRICS_DAYS=30
```

### 5. Executar o relatório FinOps

```bash
python3 src/oci_metrics_cpu_mem_media_ndays.py
```

Saídas geradas na **home do usuário**:

```text
~/Relatorio_CPU_Memoria_media_30d_multi_region.csv
~/Relatorio_CPU_Memoria_media_30d_multi_region.xlsx
```

---

## 📊 Exemplo de Recomendações

| Instância | CPU Mean | Mem Mean | Recomendação  |
|----------|----------|----------|---------------|
| vm-app01 | 9%       | 22%      | 🟥 DOWNSIZE    |
| vm-db02  | 65%      | 88%      | 🟨 UPSCALE     |
| vm-srv03 | 42%      | 51%      | 🟩 KEEP        |

---

## 🔧 Scripts disponíveis

- `oci_metrics_cpu_mem_media_ndays.py`  
  Analisa N dias de histórico e gera relatórios CSV/XLSX com recomendação FinOps.

- `oci_metrics_cpu_mem_realtime.py`  
  Consulta rápida das métricas de CPU/Memória dos últimos 30 minutos para instâncias em execução.

---

## 🤝 Contribuindo

Pull Requests são bem-vindos!  
Sugestões podem ser enviadas na aba **Issues** do repositório.

---

## 📜 Licença

Distribuído sob a licença **MIT**. Você pode usar este código em ambientes pessoais ou corporativos.
