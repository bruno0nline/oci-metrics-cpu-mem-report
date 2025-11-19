
# 🧩 OCI FinOps CPU/MEM Analyzer — Guia Interno

## Objetivo
Coletar métricas históricas de CPU/Memória de todas as instâncias OCI e gerar relatório com recomendações FinOps.

## Execução rápida

1. Clonar o repositório:

```bash
git clone https://github.com/bruno0nline/oci-metrics-cpu-mem-report.git
cd oci-metrics-cpu-mem-report
```

2. Configurar Python:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. Definir o período (dias):

```bash
export METRICS_DAYS=30
```

4. Executar o relatório:

```bash
python3 src/oci_metrics_cpu_mem_media_ndays.py
```

## Saídas geradas

- CSV: `~/Relatorio_CPU_Memoria_media_30d_multi_region.csv`
- XLSX: `~/Relatorio_CPU_Memoria_media_30d_multi_region.xlsx`

## Recomendações automáticas

- 🟩 `KEEP` — manter a configuração atual
- 🟥 `DOWNSIZE*` — forte candidato a redução de recursos
- 🟨 `UPSCALE` — indica possível gargalo (avaliar aumento de recursos)

## Erros comuns

| Erro                  | Causa provável                      | Solução                           |
|-----------------------|--------------------------------------|-----------------------------------|
| 429 TooManyRequests   | Muitas chamadas à API de Monitoring | Script já faz backoff automático |
| profile not found     | Config ~/.oci/config ausente        | Configurar perfil OCI            |
| openpyxl not found    | Dependência ausente                 | `pip install openpyxl`           |
