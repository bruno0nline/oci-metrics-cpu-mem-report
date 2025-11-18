import oci
import csv
from datetime import datetime, timedelta, timezone
from oci.monitoring.models import SummarizeMetricsDataDetails

cfg = oci.config.from_file()

compute = oci.core.ComputeClient(cfg)
monitoring = oci.monitoring.MonitoringClient(cfg)

compartment_id = cfg["tenancy"]

end = datetime.now(timezone.utc)
start = end - timedelta(minutes=15)

def get_metric(query):
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
    if resp.data and resp.data[0].aggregated_datapoints:
        dps_sorted = sorted(resp.data[0].aggregated_datapoints, key=lambda x: x.timestamp)
        return dps_sorted[-1].value
    return None

# lista de instâncias
instances = oci.pagination.list_call_get_all_results(
    compute.list_instances,
    compartment_id=compartment_id
).data

instances = [i for i in instances if i.lifecycle_state == "RUNNING"]

rows = []

for inst in instances:
    cpu_query = f'CpuUtilization[5m]{{resourceId = "{inst.id}"}}.mean()'
    mem_query = f'MemoryUtilization[5m]{{resourceId = "{inst.id}"}}.mean()'

    cpu = get_metric(cpu_query)
    mem = get_metric(mem_query)

    # detalhes da forma (shape)
    shape = inst.shape
    ocpus = inst.shape_config.ocpus if inst.shape_config else None
    mem_gb = inst.shape_config.memory_in_gbs if inst.shape_config else None

    rows.append({
        "instance_name": inst.display_name,
        "instance_ocid": inst.id,
        "shape": shape,
        "ocpus": ocpus,
        "memory_gb": mem_gb,
        "cpu_percent": round(cpu, 2) if cpu is not None else "no-data",
        "mem_percent": round(mem, 2) if mem is not None else "no-data"
    })

csv_file = "Relatorio_CPU_Memoria.csv"

with open(csv_file, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print(f"Relatório gerado: {csv_file}")
