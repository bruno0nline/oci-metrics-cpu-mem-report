
import os
import csv
import time
from datetime import datetime, timedelta, timezone

import oci
from oci.monitoring.models import SummarizeMetricsDataDetails

from openpyxl import Workbook
from openpyxl.styles import PatternFill

# ===== CONFIGURAÇÕES =====
DAYS = int(os.getenv("METRICS_DAYS", "30"))   # dias de análise
INTERVAL = "1h"                               # granularidade das métricas
OUTPUT_DIR = os.path.expanduser("~")          # salvar na home do usuário

CSV_FILE = os.path.join(
    OUTPUT_DIR, f"Relatorio_CPU_Memoria_media_{DAYS}d_multi_region.csv"
)
XLSX_FILE = os.path.join(
    OUTPUT_DIR, f"Relatorio_CPU_Memoria_media_{DAYS}d_multi_region.xlsx"
)

# Limiares FinOps
CPU_LOW = 20.0
CPU_HIGH = 70.0
MEM_LOW = 40.0
MEM_HIGH = 80.0
# =========================

cfg = oci.config.from_file()
tenancy_id = cfg["tenancy"]
identity = oci.identity.IdentityClient(cfg)

# Regiões assinadas na tenancy
regions = identity.list_region_subscriptions(tenancy_id).data

# Compartimentos (root + filhos)
compartments = oci.pagination.list_call_get_all_results(
    identity.list_compartments,
    tenancy_id,
    compartment_id_in_subtree=True,
    access_level="ANY",
).data
compartments.append(identity.get_compartment(tenancy_id).data)  # root

now = datetime.now(timezone.utc)
start = now - timedelta(days=DAYS)
end = now


def calc_mean_p95(values):
    if not values:
        return None, None
    values_sorted = sorted(values)
    n = len(values_sorted)
    mean = sum(values_sorted) / n
    idx_p95 = int(n * 0.95) - 1
    idx_p95 = max(0, min(idx_p95, n - 1))
    p95 = values_sorted[idx_p95]
    return mean, p95


def get_metric_stats(monitoring_client, compartment_id, inst_id, metric_name):
    query = f'{metric_name}[{INTERVAL}]{{resourceId = "{inst_id}"}}.mean()'
    details = SummarizeMetricsDataDetails(
        namespace="oci_computeagent",
        query=query,
        start_time=start,
        end_time=end,
    )

    max_retries = 4
    resp = None

    for attempt in range(1, max_retries + 1):
        try:
            resp = monitoring_client.summarize_metrics_data(
                compartment_id=compartment_id,
                summarize_metrics_data_details=details,
            )
            break
        except oci.exceptions.ServiceError as e:
            if e.status == 429:
                wait = 5 * (2 ** (attempt - 1))
                print(
                    f"      - 429 TooManyRequests para {metric_name}, "
                    f"tentativa {attempt}/{max_retries}, aguardando {wait}s..."
                )
                time.sleep(wait)
                continue
            print(f"      - Erro ao consultar {metric_name}: {e.message}")
            return None, None

    if resp is None or not resp.data or not resp.data[0].aggregated_datapoints:
        return None, None

    dps = resp.data[0].aggregated_datapoints
    values = [dp.value for dp in dps if dp.value is not None]

    if not values:
        return None, None

    return calc_mean_p95(values)


def classify_cpu(cpu_mean, cpu_p95):
    if cpu_mean is None:
        return "NO-DATA"
    metric = max(cpu_mean, cpu_p95 or cpu_mean)
    if metric < CPU_LOW:
        return "LOW"
    if metric > CPU_HIGH:
        return "HIGH"
    return "OK"


def classify_mem(mem_mean, mem_p95):
    if mem_mean is None:
        return "NO-DATA"
    metric = max(mem_mean, mem_p95 or mem_mean)
    if metric < MEM_LOW:
        return "LOW"
    if metric > MEM_HIGH:
        return "HIGH"
    return "OK"


def finops_recommendation(cpu_flag, mem_flag):
    if cpu_flag == "HIGH" or mem_flag == "HIGH":
        return "UPSCALE"
    if cpu_flag == "LOW" and mem_flag == "LOW":
        return "DOWNSIZE-STRONG"
    if cpu_flag == "LOW":
        return "DOWNSIZE"
    if mem_flag == "LOW":
        return "DOWNSIZE-MEM"
    return "KEEP"


def generate_excel(headers, rows):
    wb = Workbook()
    ws = wb.active
    ws.title = "FinOps_CPU_Mem"

    ws.append(headers)

    green = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
    red   = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
    yellow= PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")

    rec_col = headers.index("finops_recommendation") + 1

    for row in rows:
        ws.append([row[h] for h in headers])
        rec = row["finops_recommendation"]
        r = ws.max_row

        if rec == "KEEP":
            ws.cell(row=r, column=rec_col).fill = green
        elif rec == "UPSCALE":
            ws.cell(row=r, column=rec_col).fill = yellow
        elif rec.startswith("DOWNSIZE"):
            ws.cell(row=r, column=rec_col).fill = red

    wb.save(XLSX_FILE)


def main():
    rows = []
    idx = 0

    print(f"Coletando CPU/Mem dos últimos {DAYS} dias...\n")

    for region in regions:
        region_name = region.region_name
        print(f"\n===== Região: {region_name} =====")

        region_cfg = dict(cfg)
        region_cfg["region"] = region_name
        compute = oci.core.ComputeClient(region_cfg)
        monitoring = oci.monitoring.MonitoringClient(region_cfg)

        for compartment in compartments:
            comp_id = compartment.id
            comp_name = compartment.name

            try:
                instances = oci.pagination.list_call_get_all_results(
                    compute.list_instances,
                    compartment_id=comp_id,
                ).data
            except Exception as e:
                print(f"  [!] Erro ao listar instâncias em '{comp_name}': {e}")
                continue

            running = [i for i in instances if i.lifecycle_state == 'RUNNING']
            if not running:
                continue

            print(f"  Compartimento: {comp_name} | RUNNING: {len(running)}")

            for inst in running:
                idx += 1
                print(f"    [{idx}] {inst.display_name}")

                shape = inst.shape
                ocpus = inst.shape_config.ocpus if inst.shape_config else None
                mem_gb = inst.shape_config.memory_in_gbs if inst.shape_config else None

                cpu_mean, cpu_p95 = get_metric_stats(
                    monitoring, inst.compartment_id, inst.id, "CpuUtilization"
                )

                mem_mean, mem_p95 = get_metric_stats(
                    monitoring, inst.compartment_id, inst.id, "MemoryUtilization"
                )

                cpu_flag = classify_cpu(cpu_mean, cpu_p95)
                mem_flag = classify_mem(mem_mean, mem_p95)
                recommendation = finops_recommendation(cpu_flag, mem_flag)

                rows.append({
                    "region": region_name,
                    "compartment": comp_name,
                    "instance_name": inst.display_name,
                    "instance_ocid": inst.id,
                    "shape": shape,
                    "ocpus": ocpus,
                    "memory_gb": mem_gb,
                    "cpu_mean_percent": round(cpu_mean, 2) if cpu_mean else "no-data",
                    "cpu_p95_percent": round(cpu_p95, 2) if cpu_p95 else "no-data",
                    "mem_mean_percent": round(mem_mean, 2) if mem_mean else "no-data",
                    "mem_p95_percent": round(mem_p95, 2) if mem_p95 else "no-data",
                    "cpu_flag": cpu_flag,
                    "mem_flag": mem_flag,
                    "finops_recommendation": recommendation,
                })

    if not rows:
        print("Nenhuma instância encontrada.")
        return

    headers = list(rows[0].keys())

    # CSV
    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

    # Excel com cores
    generate_excel(headers, rows)

    print("\n✅ Relatórios gerados:")
    print(f"➡ CSV : {CSV_FILE}")
    print(f"➡ XLSX: {XLSX_FILE}")


if __name__ == "__main__":
    main()
