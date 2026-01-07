
import os
import time
import csv
from datetime import datetime, timedelta, timezone

import oci
from oci.monitoring.models import SummarizeMetricsDataDetails
from openpyxl import Workbook
from openpyxl.styles import PatternFill

cfg = oci.config.from_file()
tenancy_id = cfg["tenancy"]
homedir = os.path.expanduser("~")

DAYS = int(os.getenv("METRICS_DAYS", "30"))

CSV_PATH = os.path.join(homedir, f"Relatorio_CPU_Memoria_media_{DAYS}d_multi_region.csv")
XLSX_PATH = os.path.join(homedir, f"Relatorio_CPU_Memoria_media_{DAYS}d_multi_region.xlsx")

MAX_RETRIES = 3
RETRY_SLEEP = 3


def get_all_regions(identity_client):
    resp = identity_client.list_region_subscriptions(tenancy_id)
    return [r.region_name for r in resp.data]


def get_all_compartments(identity_client):
    result = oci.pagination.list_call_get_all_results(
        identity_client.list_compartments,
        tenancy_id,
        compartment_id_in_subtree=True
    )
    return [c for c in result.data if c.lifecycle_state == "ACTIVE"]


def summarize_with_retry(monitoring, details, compartment_ocid):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return monitoring.summarize_metrics_data(
                compartment_id=compartment_ocid,
                summarize_metrics_data_details=details,
            )
        except oci.exceptions.ServiceError as e:
            if e.status == 429 and attempt < MAX_RETRIES:
                print(f"  - 429 TooManyRequests para {details.query}, tentativa {attempt}/{MAX_RETRIES}, aguardando {RETRY_SLEEP}s...")
                time.sleep(RETRY_SLEEP)
                continue
            raise


def extract_mean_and_p95(datapoints):
    values = [dp.value for dp in datapoints if dp.value is not None]
    if not values:
        return None, None
    values_sorted = sorted(values)
    mean = sum(values_sorted) / len(values_sorted)
    idx = int(round(0.95 * (len(values_sorted) - 1)))
    p95 = values_sorted[idx]
    return mean, p95


def get_metric_stats(monitoring, compartment_ocid, inst_id, metric_name, start, end):
    query = f'{metric_name}[5m]{{resourceId = "{inst_id}"}}.mean()'
    details = SummarizeMetricsDataDetails(
        namespace="oci_computeagent",
        query=query,
        start_time=start,
        end_time=end,
    )
    resp = summarize_with_retry(monitoring, details, compartment_ocid)
    if not resp.data or not resp.data[0].aggregated_datapoints:
        return None, None
    return extract_mean_and_p95(resp.data[0].aggregated_datapoints)


def get_burstable_info(instance):
    # baseline_ocpu_utilization:
    #   - None           -> não expansível
    #   - BASELINE_1_8   -> 12.5%
    #   - BASELINE_1_2   -> 50%
    #   - BASELINE_1_1   -> 100% (instância regular)
    baseline = getattr(instance, "baseline_ocpu_utilization", None)
    if not baseline:
        return "NO", "Desativada"

    mapping = {
        "BASELINE_1_8": "12.5%",
        "BASELINE_1_2": "50%",
        "BASELINE_1_1": "100%",
    }
    perc = mapping.get(baseline, baseline)
    enabled = "YES" if baseline in mapping else "NO"
    return enabled, perc


def finops_recommendation(cpu_mean, cpu_p95, mem_mean, mem_p95):
    if cpu_mean is None and mem_mean is None:
        return "KEEP"

    cpu_mean = cpu_mean or 0
    cpu_p95 = cpu_p95 or 0
    mem_mean = mem_mean or 0
    mem_p95 = mem_p95 or 0

    if cpu_mean < 5 and mem_mean < 40:
        return "DOWNSIZE-STRONG"
    if cpu_mean < 15 and mem_mean < 60:
        return "DOWNSIZE"
    if cpu_mean < 25 and mem_mean < 40:
        return "DOWNSIZE-MEM"

    if cpu_p95 > 80 or mem_p95 > 85:
        return "UPSCALE"

    return "KEEP"


def main():
    identity = oci.identity.IdentityClient(cfg)
    regions = get_all_regions(identity)
    compartments = get_all_compartments(identity)

    start = datetime.now(timezone.utc) - timedelta(days=DAYS)
    end = datetime.now(timezone.utc)

    print(f"Coletando médias de CPU/Mem dos últimos {DAYS} dias...")
    print(f"Total de compartments ativos: {len(compartments)}")

    rows = []

    for region in regions:
        print(f"\n===== Região: {region} =====")
        region_cfg = dict(cfg)
        region_cfg["region"] = region

        compute = oci.core.ComputeClient(region_cfg)
        monitoring = oci.monitoring.MonitoringClient(region_cfg)

        for comp in compartments:
            comp_id = comp.id
            comp_name = comp.name

            try:
                instances = oci.pagination.list_call_get_all_results(
                    compute.list_instances,
                    compartment_id=comp_id
                ).data
            except oci.exceptions.ServiceError as e:
                print(f"  [WARN] Erro ao listar instâncias no compartment {comp_name}: {e}")
                continue

            running = [i for i in instances if i.lifecycle_state == "RUNNING"]
            if not running:
                continue

            print(f"  Compartment: {comp_name} | Instâncias RUNNING: {len(running)}")

            for inst in running:
                print(f"  -> [{inst.display_name}]")

                cpu_mean, cpu_p95 = get_metric_stats(
                    monitoring,
                    comp_id,
                    inst.id,
                    "CpuUtilization",
                    start,
                    end,
                )
                mem_mean, mem_p95 = get_metric_stats(
                    monitoring,
                    comp_id,
                    inst.id,
                    "MemoryUtilization",
                    start,
                    end,
                )

                shape = inst.shape
                ocpus = getattr(inst.shape_config, "ocpus", None) if inst.shape_config else None
                mem_gb = getattr(inst.shape_config, "memory_in_gbs", None) if inst.shape_config else None

                burstable_enabled, baseline_percent = get_burstable_info(inst)
                baseline_raw = getattr(inst, "baseline_ocpu_utilization", None) or ""

                rec = finops_recommendation(cpu_mean, cpu_p95, mem_mean, mem_p95)

                rows.append({
                    "region": region,
                    "compartment": comp_name,
                    "instance_name": inst.display_name,
                    "instance_ocid": inst.id,
                    "shape": shape,
                    "ocpus": ocpus,
                    "memory_gb": mem_gb,
                    "burstable_enabled": burstable_enabled,
                    "baseline_percent": baseline_percent,
                    "baseline_raw": baseline_raw,
                    "cpu_mean_percent": cpu_mean,
                    "cpu_p95_percent": cpu_p95,
                    "mem_mean_percent": mem_mean,
                    "mem_p95_percent": mem_p95,
                    "finops_recommendation": rec,
                })

    if not rows:
        print("Nenhuma instância RUNNING encontrada na tenancy.")
        return

    fieldnames = [
        "region",
        "compartment",
        "instance_name",
        "instance_ocid",
        "shape",
        "ocpus",
        "memory_gb",
        "burstable_enabled",
        "baseline_percent",
        "baseline_raw",
        "cpu_mean_percent",
        "cpu_p95_percent",
        "mem_mean_percent",
        "mem_p95_percent",
        "finops_recommendation",
    ]

    with open(CSV_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    print(f"\n✅ CSV gerado: {CSV_PATH}")

    wb = Workbook()
    ws = wb.active
    ws.title = "CPU_Mem_FinOps"

    ws.append(fieldnames)

    fill_keep = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
    fill_down = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
    fill_up = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
    fill_header = PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid")

    for cell in ws[1]:
        cell.fill = fill_header

    for r in rows:
        ws.append([r[col] for col in fieldnames])
        row_idx = ws.max_row
        rec = r["finops_recommendation"]

        if rec.startswith("DOWNSIZE"):
            style = fill_down
        elif rec == "UPSCALE":
            style = fill_up
        else:
            style = fill_keep

        ws[f"P{row_idx}"].fill = style

    wb.save(XLSX_PATH)
    print(f"✅ XLSX gerado: {XLSX_PATH}")


if __name__ == "__main__":
    main()
