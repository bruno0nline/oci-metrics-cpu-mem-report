def get_top5(rows):
    savings = []
    costs = []

    for r in rows:
        rec = r["finops_recommendation"]
        value = float(r.get("monthly_savings_brl", 0))

        if value <= 0:
            continue

        if rec.startswith("DOWNSIZE") or "BURSTABLE" in rec:
            savings.append((r, value))
        elif rec == "UPSCALE":
            costs.append((r, value))

    top5_savings = sorted(savings, key=lambda x: x[1], reverse=True)[:5]
    top5_costs = sorted(costs, key=lambda x: x[1], reverse=True)[:5]

    return top5_savings, top5_costs
