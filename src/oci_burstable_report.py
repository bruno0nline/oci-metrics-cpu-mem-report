import os
import csv
import oci

HOME = os.path.expanduser("~")
CSV_PATH = os.path.join(HOME, "Relatorio_Burstable_OCI.csv")

cfg = oci.config.from_file()
tenancy_id = cfg["tenancy"]
identity = oci.identity.IdentityClient(cfg)


def get_regions():
    return [r.region_name for r in identity.list_region_subscriptions(tenancy_id).data]


def get_compartments():
    comps = oci.pagination.list_call_get_all_results(
        identity.list_compartments,
        tenancy_id,
        compartment_id_in_subtree=True
    ).data
    root = identity.get_compartment(tenancy_id).data
    return [c for c in comps if c.lifecycle_state == "ACTIVE"] + [root]


def parse_baseline(inst):
    baseline = getattr(inst, "baseline_ocpu_utilization", None)
    if baseline is None:
        return "NO", "Desativada", ""

    mapping = {
        "BASELINE_1_8": "12.5%",
        "BASELINE_1_2": "50%",
        "BASELINE_1_1": "100%",
    }

    return "YES", mapping.get(baseline, baseline), baseline


def main():
    regions = get_regions()
    compartments = get_compartments()

    rows = []

    print("\n⚡ Coletando configuração de Burstable\n")

    for region in regions:
        print(f"🟢 Região: {region}")
        cfg_r = dict(cfg)
        cfg_r["region"] = region

        compute = oci.core.ComputeClient(cfg_r)

        for comp in compartments:
            try:
                instances = oci.pagination.list_call_get_all_results(
                    compute.list_instances,
                    compartment_id=comp.id
                ).data
            except oci.exceptions.ServiceError:
                print(f"⚠️ Sem acesso ao compartment {comp.name}")
                continue

            for inst in instances:
                burst, baseline_percent, baseline_raw = parse_baseline(inst)

                rows.append({
                    "region": region,
                    "compartment": comp.name,
                    "instance_name": inst.display_name,
                    "shape": inst.shape,
                    "ocpus": getattr(inst.shape_config, "ocpus", None),
                    "memory_gb": getattr(inst.shape_config, "memory_in_gbs", None),
                    "burstable_enabled": burst,
                    "baseline_percent": baseline_percent,
                    "baseline_raw": baseline_raw,
                })

    headers = list(rows[0].keys())

    with open(CSV_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

    print("\n✅ Relatório Burstable gerado:")
    print(f"➡ CSV : {CSV_PATH}")


if __name__ == "__main__":
    main()
