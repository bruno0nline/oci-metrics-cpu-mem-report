import os
import csv
from datetime import datetime, timedelta, timezone

import oci
from oci.monitoring.models import SummarizeMetricsDataDetails

# ===== CONFIGURAÇÕES =====
# Dias de histórico (pode sobrescrever com METRICS_DAYS=30 no ambiente)
DAYS = int(os.getenv("METRICS_DAYS", "30"))
INTERVAL = "1h"  # resolução das métricas
CSV_FILE = f"Relatorio_CPU_Memoria_media_{DAYS}d.csv"
# =========================

cfg = oci.config.from_file()

compute = oci.core.ComputeClient(cfg)
monitoring = oci.monitoring.MonitoringClient(cfg)

compartment_id = cfg["tenancy"]

now = datetime.now(timezone.utc)
start = now - timedelta(days=DAYS)
end = now

def get_metric_mean(inst_id, metric_name):
    """
    metric_name: "CpuUtilization" ou "MemoryUtilization"
    Retorna média dos valores no período ou None.
    """
    query = f'{metric_name}[{INTERVAL}]{{resourceId = "{inst_id}"}}.mean()'
    details = SummarizeMetricsDataDetails(
        namespace="oci_computeagent",
        query=query,
        start_time=start,
        end_time=end
    )

    resp = monitoring.summarize_metrics_data(
        compartment_id=compartment_id,
        summarize_metrics_data_details=details
    )

    if not resp.data or not resp.data[0].aggregated_datapoints:
        return None

    dps = resp.data[0].aggregated_datapoints
    values = [dp.value for dp in dps if dp.value is not None]

    if not values:
        return None

    return sum(values) / len(values)

# Lista instâncias em RUNNING
instances = oci.pagination.list_call_get_all_results(
    compute.list_instances,
    compartment_id=compartment_id
).data

instances = [i for i in instances if i.lifecycle_state == "RUNNING"]

if not instances:
    print("Nenhuma instância em RUNNING no compartimento.")
    raise SystemExit(0)

print(f"Coletando médias de CPU/Mem dos últimos {DAYS} dias...")
print(f"Total de instâncias em RUNNING: {len(instances)}\n")

rows = []
total = len(instances)

for idx, inst in enumerate(instances, start=1):
    name = inst.display_name

    # Detalhes de shape
    shape = inst.shape
    ocpus = inst.shape_config.ocpus if inst.shape_config else None
    mem_gb = inst.shape_config.memory_in_gbs if inst.shape_config else None

    print(f"[{idx}/{total}] {name}:")
    cpu_mean = get_metric_mean(inst.id, "CpuUtilization")
    print(f"  - CPU média   : {cpu_mean:.2f} %" if cpu_mean is not None else "  - CPU média   : sem dados")

    mem_mean = get_metric_mean(inst.id, "MemoryUtilization")
    print(f"  - Mem média   : {mem_mean:.2f} %" if mem_mean is not None else "  - Mem média   : sem dados")

    rows.append({
        "instance_name": name,
        "instance_ocid": inst.id,
        "shape": shape,
        "ocpus": ocpus,
        "memory_gb": mem_gb,
        "cpu_mean_percent": round(cpu_mean, 2) if cpu_mean is not None else "no-data",
        "mem_mean_percent": round(mem_mean, 2) if mem_mean is not None else "no-data",
    })

# Gera CSV
with open(CSV_FILE, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print(f"\n✅ Relatório gerado: {CSV_FILE}")

