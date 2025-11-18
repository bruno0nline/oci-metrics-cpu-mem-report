import os
import csv
from datetime import datetime, timedelta, timezone

import oci
from oci.monitoring.models import SummarizeMetricsDataDetails

# ===== CONFIGURAÇÕES =====
# Dias de histórico (pode sobrescrever com METRICS_DAYS=30 no ambiente)
DAYS = int(os.getenv("METRICS_DAYS", "30"))
INTERVAL = "1h"  # resolução das métricas
CSV_FILE = f"Relatorio_CPU_Memoria_media_{DAYS}d_multi_region.csv"
# =========================


cfg = oci.config.from_file()
tenancy_id = cfg["tenancy"]

identity = oci.identity.IdentityClient(cfg)

# Regiões assinadas no tenancy
regions = identity.list_region_subscriptions(tenancy_id).data

# Compartimentos (raiz + todos os filhos)
compartments = oci.pagination.list_call_get_all_results(
    identity.list_compartments,
    tenancy_id,
    compartment_id_in_subtree=True,
    access_level="ANY"
).data
compartments.append(identity.get_compartment(tenancy_id).data)  # root


now = datetime.now(timezone.utc)
start = now - timedelta(days=DAYS)
end = now


def get_metric_mean(monitoring_client, compartment_id, inst_id, metric_name):
    """
    metric_name: "CpuUtilization" ou "MemoryUtilization"
    Retorna média dos valores no período ou None.
    """
    query = f'{metric_name}[{INTERVAL}]{{resourceId = "{inst_id}"}}.mean()'
    details = SummarizeMetricsDataDetails(
        namespace="oci_computeagent",
        query=query,
        start_time=start,
        end_time=end,
    )

    resp = monitoring_client.summarize_metrics_data(
        compartment_id=compartment_id,
        summarize_metrics_data_details=details,
    )

    if not resp.data or not resp.data[0].aggregated_datapoints:
        return None

    dps = resp.data[0].aggregated_datapoints
    values = [dp.value for dp in dps if dp.value is not None]

    if not values:
        return None

    return sum(values) / len(values)


def main():
    rows = []
    idx = 0

    print(f"Coletando médias de CPU/Mem dos últimos {DAYS} dias...")
    print("Varredura: TODAS as regiões e TODOS os compartments do tenancy.\n")

    for region in regions:
        region_name = region.region_name
        print(f"\n===== Região: {region_name} =====")

        # ajusta config pra região atual
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
            except oci.exceptions.ServiceError as e:
                print(f"  [!] Erro ao listar instâncias em '{comp_name}' ({region_name}): {e}")
                continue

            running = [i for i in instances if i.lifecycle_state == "RUNNING"]
            if not running:
                continue

            print(f"  Compartimento: {comp_name} | Instâncias RUNNING: {len(running)}")

            for inst in running:
                idx += 1
                name = inst.display_name
                shape = inst.shape
                ocpus = inst.shape_config.ocpus if inst.shape_config else None
                mem_gb = inst.shape_config.memory_in_gbs if inst.shape_config else None

                print(f"    [{idx}] {name}")

                cpu_mean = get_metric_mean(
                    monitoring_client=monitoring,
                    compartment_id=inst.compartment_id,
                    inst_id=inst.id,
                    metric_name="CpuUtilization",
                )
                print(
                    f"      - CPU média : {cpu_mean:.2f} %"
                    if cpu_mean is not None
                    else "      - CPU média : sem dados"
                )

                mem_mean = get_metric_mean(
                    monitoring_client=monitoring,
                    compartment_id=inst.compartment_id,
                    inst_id=inst.id,
                    metric_name="MemoryUtilization",
                )
                print(
                    f"      - Mem média : {mem_mean:.2f} %"
                    if mem_mean is not None
                    else "      - Mem média : sem dados"
                )

                rows.append(
                    {
                        "region": region_name,
                        "compartment": comp_name,
                        "instance_name": name,
                        "instance_ocid": inst.id,
                        "shape": shape,
                        "ocpus": ocpus,
                        "memory_gb": mem_gb,
                        "cpu_mean_percent": round(cpu_mean, 2)
                        if cpu_mean is not None
                        else "no-data",
                        "mem_mean_percent": round(mem_mean, 2)
                        if mem_mean is not None
                        else "no-data",
                    }
                )

    if not rows:
        print("\n⚠️ Nenhuma instância RUNNING encontrada em nenhuma região/compartment.")
        return

    # Gera CSV
    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n✅ Relatório gerado: {CSV_FILE}")


if __name__ == "__main__":
    main()

