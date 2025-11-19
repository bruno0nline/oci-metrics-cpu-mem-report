
import os
from datetime import datetime, timedelta, timezone

import oci
from oci.monitoring.models import SummarizeMetricsDataDetails

INTERVAL = "5m"

cfg = oci.config.from_file()
tenancy_id = cfg["tenancy"]
identity = oci.identity.IdentityClient(cfg)
regions = identity.list_region_subscriptions(tenancy_id).data

now = datetime.now(timezone.utc)
start = now - timedelta(minutes=30)
end = now


def main():
    print("Relatório rápido de CPU/Mem (últimos 30 minutos)...\n")

    for region in regions:
        region_name = region.region_name
        print(f"=== Região: {region_name} ===")
        region_cfg = dict(cfg)
        region_cfg["region"] = region_name

        compute = oci.core.ComputeClient(region_cfg)
        monitoring = oci.monitoring.MonitoringClient(region_cfg)

        instances = oci.pagination.list_call_get_all_results(
            compute.list_instances,
            compartment_id=tenancy_id,
        ).data

        running = [i for i in instances if i.lifecycle_state == 'RUNNING']
        if not running:
            print("  Nenhuma instância RUNNING.\n")
            continue

        for inst in running:
            print(f"- {inst.display_name} ({inst.id})")

            for metric in ("CpuUtilization", "MemoryUtilization"):
                query = f'{metric}[{INTERVAL}]{{resourceId = "{inst.id}"}}.mean()'
                details = SummarizeMetricsDataDetails(
                    namespace="oci_computeagent",
                    query=query,
                    start_time=start,
                    end_time=end,
                )

                resp = monitoring.summarize_metrics_data(
                    compartment_id=inst.compartment_id,
                    summarize_metrics_data_details=details,
                )

                if not resp.data or not resp.data[0].aggregated_datapoints:
                    print(f"  {metric}: sem dados")
                    continue

                last = resp.data[0].aggregated_datapoints[-1]
                print(f"  {metric}: {last.value:.2f} % (timestamp {last.timestamp})")
            print()

if __name__ == "__main__":
    main()
