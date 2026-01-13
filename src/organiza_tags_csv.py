import csv
import json
import os
from openpyxl import Workbook

# ================= CONFIG =================
HOME = os.path.expanduser("~")

INPUT_CSV = os.path.join(HOME, "Relatorio_Instancias_Tags_OCI.csv")
OUT_CSV = os.path.join(HOME, "Relatorio_Instancias_Tags_Organizado.csv")
OUT_XLSX = os.path.join(HOME, "Relatorio_Instancias_Tags_Organizado.xlsx")
# =========================================


def parse_json(value):
    try:
        return json.loads(value) if value else {}
    except Exception:
        return {}


def main():
    with open(INPUT_CSV, newline="", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))

    # ---------------- descobrir TODAS as chaves ----------------
    freeform_keys = set()
    defined_keys = set()

    for r in reader:
        freeform = parse_json(r.get("freeform_tags") or r.get("all_freeform_tags"))
        defined = parse_json(r.get("defined_tags"))

        oracle_tags = defined.get("Oracle-Tags", {}) if isinstance(defined, dict) else {}

        freeform_keys.update(freeform.keys())
        defined_keys.update(oracle_tags.keys())

    freeform_keys = sorted(freeform_keys)
    defined_keys = sorted(defined_keys)

    # ---------------- montar linhas novas ----------------
    rows_out = []

    for r in reader:
        freeform = parse_json(r.get("freeform_tags") or r.get("all_freeform_tags"))
        defined = parse_json(r.get("defined_tags"))
        oracle_tags = defined.get("Oracle-Tags", {}) if isinstance(defined, dict) else {}

        row = dict(r)  # mantém tudo original

        # explode freeform tags
        for k in freeform_keys:
            row[f"freeform_{k}"] = freeform.get(k, "")

        # explode defined tags (Oracle-Tags)
        for k in defined_keys:
            row[f"defined_{k}"] = oracle_tags.get(k, "")

        rows_out.append(row)

    # ---------------- CSV ----------------
    headers = list(rows_out[0].keys())

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows_out)

    # ---------------- XLSX ----------------
    wb = Workbook()
    ws = wb.active
    ws.title = "INSTANCIAS_TAGS"

    ws.append(headers)

    for r in rows_out:
        ws.append([r[h] for h in headers])

    ws.auto_filter.ref = ws.dimensions
    ws.freeze_panes = "A2"

    wb.save(OUT_XLSX)

    print("\n✅ Tags organizadas com sucesso:")
    print(f"➡ CSV : {OUT_CSV}")
    print(f"➡ XLSX: {OUT_XLSX}")
    print(f"📌 Freeform tags encontradas: {len(freeform_keys)}")
    print(f"📌 Defined (Oracle-Tags) encontradas: {len(defined_keys)}")


if __name__ == "__main__":
    main()
