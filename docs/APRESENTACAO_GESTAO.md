
# 📘 Relatório — Projeto OCI FinOps Analyzer

## Resumo Executivo

O projeto **OCI FinOps Analyzer** oferece uma visão consolidada do uso de CPU e Memória das instâncias de Compute na Oracle Cloud Infrastructure (OCI), permitindo identificar oportunidades de redução de custos (FinOps) e necessidades de ajuste de capacidade (upsizing).

## Benefícios para o negócio

- 💰 **Redução de custos** com identificação de servidores superdimensionados.
- 🚀 **Melhoria de performance** com indicação de instâncias que precisam de mais recursos.
- 📊 **Visão centralizada** de múltiplas regiões e compartments.
- 🧾 **Relatórios padronizados** em CSV e Excel, prontos para auditorias e apresentações.
- 🔁 **Processo repetível** e automatizável (pode ser agendado).

## Como funciona

1. O script é executado a partir do **OCI Cloud Shell** ou servidor com OCI CLI/SDK configurado.
2. Ele lê as configurações do arquivo `~/.oci/config`.
3. Varre todas as **regiões ativas** da tenancy.
4. Em cada região, percorre **todos os compartments** (raiz e filhos).
5. Para cada instância em estado **RUNNING**, coleta:
   - Uso médio de CPU e Memória (N dias)
   - Percentil 95 (P95) de CPU e Memória
6. Classifica cada servidor em categorias FinOps:
   - `KEEP` — manter como está
   - `DOWNSIZE*` — candidato a redução de recursos
   - `UPSCALE` — possível gargalo
7. Gera dois arquivos na home do operador:
   - CSV detalhado
   - Planilha Excel com cores por recomendação

## Uso típico

- Execução mensal ou semanal como parte do processo de **FinOps da empresa**.
- Base para reuniões de:
  - Governança de Cloud
  - Revisão de custos
  - Planejamento de capacidade

## Próximos passos sugeridos

- Integrar os relatórios com dashboards (Power BI, Grafana, etc.).
- Criar jobs agendados para geração automática dos relatórios.
- Evoluir o motor de regras para incluir disco, rede e SLAs de aplicações.

