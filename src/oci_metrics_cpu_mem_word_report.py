
import os
import csv
from datetime import datetime

from docx import Document
from docx.shared import Pt

homedir = os.path.expanduser("~")
DAYS = int(os.getenv("METRICS_DAYS", "30"))

CSV_PATH = os.path.join(homedir, f"Relatorio_CPU_Memoria_media_{DAYS}d_multi_region.csv")
DOCX_PATH = os.path.join(homedir, f"Relatorio_FinOps_CPU_Mem_{DAYS}d_multi_region.docx")

# Valores aproximados por hora em USD (exemplo, ajuste se necessário)
OCPU_PRICE_HOUR = 0.05
MEM_GB_PRICE_HOUR = 0.003
HOURS_MONTH = 730


def to_float(value):
    try:
        if value is None or value == "":
            return None
        return float(value)
    except Exception:
        return None


def estimate_monthly_cost(ocpus, mem_gb):
    ocpus = ocpus or 0
    mem_gb = mem_gb or 0
    hourly = ocpus * OCPU_PRICE_HOUR + mem_gb * MEM_GB_PRICE_HOUR
    return hourly * HOURS_MONTH


def format_money_usd(v):
    return f"US$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def load_rows():
    rows = []
    if not os.path.exists(CSV_PATH):
        print(f"CSV não encontrado: {CSV_PATH}")
        return rows

    with open(CSV_PATH, newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    return rows


def build_downsize_text(row):
    inst = row["instance_name"]
    shape = row["shape"]
    region = row["region"]
    comp = row["compartment"]

    cpu_mean = to_float(row["cpu_mean_percent"]) or 0
    mem_mean = to_float(row["mem_mean_percent"]) or 0
    ocpus = to_float(row["ocpus"]) or 0
    mem_gb = to_float(row["memory_gb"]) or 0

    fator = 0.5
    if cpu_mean < 5 and mem_mean < 40:
        fator = 0.25

    new_ocpus = max(1, ocpus * fator)
    new_mem = max(1, mem_gb * fator)

    current_cost = estimate_monthly_cost(ocpus, mem_gb)
    new_cost = estimate_monthly_cost(new_ocpus, new_mem)
    savings = max(0, current_cost - new_cost)

    text = (
        f"Instância: {inst} | Região: {region} | Compartment: {comp}\n"
        f"Forma atual: {shape} | OCPUs: {ocpus} | Memória: {mem_gb} GB\n"
        f"Média CPU: {cpu_mean:.2f}% | Média Memória: {mem_mean:.2f}%\n"
        f"Sugestão: reduzir para ~{new_ocpus:.1f} OCPUs e ~{new_mem:.1f} GB de memória.\n"
        f"Economia estimada: {format_money_usd(savings)}/mês.\n"
    )
    return text, savings


def build_upscale_text(row):
    inst = row["instance_name"]
    shape = row["shape"]
    region = row["region"]
    comp = row["compartment"]

    cpu_mean = to_float(row["cpu_mean_percent"]) or 0
    mem_mean = to_float(row["mem_mean_percent"]) or 0
    cpu_p95 = to_float(row["cpu_p95_percent"]) or 0
    mem_p95 = to_float(row["mem_p95_percent"]) or 0
    ocpus = to_float(row["ocpus"]) or 0
    mem_gb = to_float(row["memory_gb"]) or 0

    fator = 2.0
    new_ocpus = ocpus * fator
    new_mem = mem_gb * fator

    current_cost = estimate_monthly_cost(ocpus, mem_gb)
    new_cost = estimate_monthly_cost(new_ocpus, new_mem)
    extra = max(0, new_cost - current_cost)

    text = (
        f"Instância: {inst} | Região: {region} | Compartment: {comp}\n"
        f"Forma atual: {shape} | OCPUs: {ocpus} | Memória: {mem_gb} GB\n"
        f"CPU média/P95: {cpu_mean:.2f}% / {cpu_p95:.2f}% | Memória média/P95: {mem_mean:.2f}% / {mem_p95:.2f}%\n"
        f"Sugestão: avaliar aumento para ~{new_ocpus:.1f} OCPUs e ~{new_mem:.1f} GB de memória.\n"
        f"Impacto estimado: +{format_money_usd(extra)}/mês.\n"
    )
    return text, extra


def build_burstable_only_text(row):
    inst = row["instance_name"]
    shape = row["shape"]
    region = row["region"]
    comp = row["compartment"]

    burst_enabled = row.get("burstable_enabled", "NO")
    baseline_percent = (row.get("baseline_percent") or "").strip()

    cpu_mean = to_float(row["cpu_mean_percent"]) or 0
    ocpus = to_float(row["ocpus"]) or 0
    mem_gb = to_float(row["memory_gb"]) or 0

    if burst_enabled == "YES" and baseline_percent in ("12.5%", "50%", "100%"):
        return None, 0.0

    target = None
    frac = None

    if cpu_mean < 8:
        target = "12.5%"
        frac = 0.125
    elif cpu_mean < 35:
        target = "50%"
        frac = 0.5

    if not target or frac is None:
        return None, 0.0

    current_cost = estimate_monthly_cost(ocpus, mem_gb)
    new_cost = estimate_monthly_cost(ocpus * frac, mem_gb)
    savings = max(0, current_cost - new_cost)

    text = (
        f"Instância: {inst} | Região: {region} | Compartment: {comp}\n"
        f"Forma: {shape} | OCPUs: {ocpus} | Burstable atual: {baseline_percent or 'Desativado'}\n"
        f"CPU média: {cpu_mean:.2f}%\n"
        f"Sugestão: avaliar conversão para instância expansível com baseline {target}.\n"
        f"Economia estimada (se convertido): {format_money_usd(savings)}/mês.\n"
    )
    return text, savings


def generate_report():
    rows = load_rows()
    if not rows:
        return

    doc = Document()
    title = doc.add_heading("Relatório FinOps – CPU, Memória e Instâncias Expansíveis (OCI)", level=0)
    title.alignment = 0

    p = doc.add_paragraph()
    run = p.add_run("Gerado automaticamente a partir das métricas OCI Monitoring. Usuário responsável: Bruno Mendes Augusto.")
    run.italic = True
    run.font.size = Pt(9)

    doc.add_paragraph("\nJanela de análise: últimos %d dias." % DAYS)

    downsizes_texts = []
    upscales_texts = []
    burst_texts = []

    total_down_savings = 0.0
    total_up_extra = 0.0
    total_burst_savings = 0.0

    doc.add_heading("1. Recomendações de Redução (Downsize)", level=1)
    for r in rows:
        rec = r.get("finops_recommendation", "")
        if rec.startswith("DOWNSIZE"):
            text, savings = build_downsize_text(r)
            downsizes_texts.append(text)
            total_down_savings += savings

    if downsizes_texts:
        for t in downsizes_texts:
            doc.add_paragraph(t)
    else:
        doc.add_paragraph("Nenhuma instância fortemente candidata a downsize identificada.")
    doc.add_paragraph(" ")

    doc.add_heading("2. Recomendações de Aumento (Upscale)", level=1)
    for r in rows:
        rec = r.get("finops_recommendation", "")
        if rec == "UPSCALE":
            text, extra = build_upscale_text(r)
            upscales_texts.append(text)
            total_up_extra += extra

    if upscales_texts:
        for t in upscales_texts:
            doc.add_paragraph(t)
    else:
        doc.add_paragraph("Nenhuma instância com forte indicação de upscale encontrada.")
    doc.add_paragraph(" ")

    doc.add_heading("3. Oportunidades para Instâncias Expansíveis (Burstable)", level=1)
    for r in rows:
        burst_text, savings = build_burstable_only_text(r)
        if burst_text:
            burst_texts.append(burst_text)
            total_burst_savings += savings

    if burst_texts:
        for t in burst_texts:
            doc.add_paragraph(t)
    else:
        doc.add_paragraph("Nenhuma oportunidade clara para conversão em instância expansível foi identificada.")
    doc.add_paragraph(" ")

    doc.add_heading("4. Resumo Financeiro Consolidado (Estimativa)", level=1)

    if total_down_savings > 0:
        doc.add_paragraph(f"1. Reduções (Downsize): economia potencial de {format_money_usd(total_down_savings)}/mês.")
    else:
        doc.add_paragraph("1. Reduções (Downsize): nenhuma economia estimada.")
    if total_up_extra > 0:
        doc.add_paragraph(f"2. Aumentos (Upscale): impacto adicional potencial de {format_money_usd(total_up_extra)}/mês.")
    else:
        doc.add_paragraph("2. Aumentos (Upscale): nenhum aumento de custo estimado.")
    if total_burst_savings > 0:
        doc.add_paragraph(f"3. Instâncias Expansíveis (Burstable): economia potencial de {format_money_usd(total_burst_savings)}/mês.")
    else:
        doc.add_paragraph("3. Instâncias Expansíveis (Burstable): nenhuma economia estimada.")    

    net = total_down_savings + total_burst_savings - total_up_extra
    if net >= 0:
        doc.add_paragraph(f"\nEconomia líquida potencial (estimada): {format_money_usd(net)}/mês.")
    else:
        doc.add_paragraph(f"\nImpacto líquido potencial (estimado): +{format_money_usd(abs(net))}/mês.")

    doc.add_paragraph("\nObservação: todos os valores são estimativas em USD baseadas em preços de tabela simplificados. Ajuste os valores de OCPU_PRICE_HOUR e MEM_GB_PRICE_HOUR conforme a realidade contratual do cliente.")

    doc.save(DOCX_PATH)
    print(f"Relatório Word gerado: {DOCX_PATH}")


if __name__ == "__main__":
    generate_report()
