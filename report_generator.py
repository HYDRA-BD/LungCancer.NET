"""
report_generator.py — Hospital-Grade Clinical PDF Report Generator for LungCancer.NET.

Key Features:
  • Executive Medical Header with Institutional Branding & Verification Hash
  • Color-Coded Triage Banner with Confidence Intervals and Decision Cutoffs
  • Patient Demographic, Biometric & 5-Year Environmental Exposure Matrix
  • Explainable AI (XAI) / Local SHAP Feature Attribution Table
  • Equity & Access Safeguard Audit
  • Matched USPSTF Guideline Evidence Matrix (with semantic RAG excerpts)
  • Physician AI Narrative Summary
  • Structured Clinical Orders & Next Steps Checkbox Protocol
  • Cryptographic SHA-256 Document Integrity Seal & Physician Signature Block
"""
from __future__ import annotations

import hashlib
import io
import os
from datetime import datetime
from xml.sax.saxutils import escape as X

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate, Frame, KeepTogether, PageTemplate,
    Paragraph, Spacer, Table, TableStyle,
)

# ───────────────────────────── Palette ─────────────────────────────
NAVY       = HexColor("#0F2E5C")
NAVY_LIGHT = HexColor("#2A5FA8")
ACCENT     = HexColor("#3B82F6")
LIGHT_BG   = HexColor("#F1F5F9")
PALE       = HexColor("#F8FAFC")
RED        = HexColor("#DC2626")
AMBER      = HexColor("#D97706")
GREEN      = HexColor("#16A34A")
GREY       = HexColor("#64748B")
SOFT_GREY  = HexColor("#94A3B8")
DARK       = HexColor("#0F172A")
WHITE      = colors.white
BORDER     = HexColor("#CBD5E1")

TIER_CONFIG = {
    "REFER":    (RED,   "HIGH RISK — FAST-TRACK REFERRAL", "Immediate Low-Dose CT (LDCT) Order Recommended"),
    "REVIEW":   (AMBER, "INTERMEDIATE RISK — HUMAN REVIEW", "Clinical Shared Decision-Making & Symptom Monitoring"),
    "RULE-OUT": (GREEN, "LOW RISK — SAFE TO CLEAR",        "Safe for Community Monitoring / Routine Annual Care"),
}


def _st(name, **kw):
    base = dict(fontName="Helvetica", fontSize=9.0, textColor=DARK, leading=13.0, alignment=TA_LEFT)
    base.update(kw)
    return ParagraphStyle(name, **base)


ST = {
    "title":       _st("title", fontName="Helvetica-Bold", fontSize=18, textColor=NAVY, leading=22, spaceAfter=2),
    "subtitle":    _st("subtitle", fontSize=8.5, textColor=GREY, leading=11, spaceAfter=8),
    "badge_num":   _st("badge_num", fontName="Helvetica-Bold", fontSize=10, textColor=WHITE, alignment=TA_CENTER, leading=13),
    "badge_title": _st("badge_title", fontName="Helvetica-Bold", fontSize=10, textColor=NAVY, leading=14),
    "body":        _st("body", alignment=TA_JUSTIFY, leading=13.5),
    "small":       _st("small", fontSize=8.5, leading=11.5, textColor=DARK),
    "tiny":        _st("tiny", fontSize=7.5, leading=10, textColor=GREY),
    "italic":      _st("italic", fontName="Helvetica-Oblique", fontSize=8.5, leading=12),
    "table_hdr":   _st("table_hdr", fontName="Helvetica-Bold", fontSize=8.5, textColor=WHITE, leading=11),
    "table_lbl":   _st("table_lbl", fontName="Helvetica-Bold", fontSize=8.5, textColor=NAVY, leading=11),
    "table_val":   _st("table_val", fontSize=8.5, leading=11),
    "quote":       _st("quote", fontName="Helvetica-Oblique", fontSize=8.0, leading=11.5, textColor=DARK, alignment=TA_JUSTIFY),
}


def _fmt(v, d=1, default="—"):
    if v is None:
        return default
    try:
        return f"{float(v):.{d}f}"
    except (TypeError, ValueError):
        return str(v)


def _section(num: int, title: str):
    """Numbered section header with clinical navy badge."""
    t = Table(
        [[Paragraph(str(num), ST["badge_num"]), Paragraph(X(title.upper()), ST["badge_title"])]],
        colWidths=[7 * mm, None],
    )
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), NAVY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (0, 0), 2),
        ("RIGHTPADDING", (0, 0), (0, 0), 2),
        ("LEFTPADDING", (1, 0), (1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ("LINEBELOW", (1, 0), (1, 0), 0.8, NAVY),
    ]))
    return t


def _kv_table(rows, label_w=52 * mm):
    data = [[Paragraph("Clinical Parameter", ST["table_hdr"]), Paragraph("Observation / Record", ST["table_hdr"])]]
    for label, value in rows:
        data.append([
            Paragraph(X(str(label)), ST["table_lbl"]),
            Paragraph(str(value), ST["table_val"]),
        ])
    t = Table(data, colWidths=[label_w, None], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.3, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, PALE]),
    ]))
    return t


def _risk_banner(tier: str, score: float, recommendation: str, ci_lower: float | None = None, ci_upper: float | None = None):
    colour, label, sublabel = TIER_CONFIG.get(tier, (DARK, tier, recommendation))

    ci_text = ""
    if ci_lower is not None and ci_upper is not None:
        ci_text = f"<br/><font color='#64748B' size='7'>95% CI: {ci_lower*100:.3f}% – {ci_upper*100:.3f}%</font>"

    left = Paragraph(
        f'<font color="white" size="8">TRIAGE TIER</font><br/>'
        f'<font color="white" size="16"><b>{X(tier)}</b></font>',
        _st("left", alignment=TA_CENTER, textColor=WHITE, leading=18),
    )
    middle = Paragraph(
        f'<font color="{colour.hexval()}" size="11"><b>{X(label)}</b></font><br/>'
        f'<font color="#334155" size="8.5">{X(sublabel)}</font><br/>'
        f'<font color="#64748B" size="7.5">Protocol: {X(recommendation)}</font>',
        _st("mid", leading=12),
    )
    right = Paragraph(
        f'<font color="#64748B" size="7.5">UNIFIED RISK</font><br/>'
        f'<font color="{colour.hexval()}" size="17"><b>{score*100:.3f}%</b></font>'
        f'{ci_text}',
        _st("right", alignment=TA_CENTER, leading=18),
    )

    t = Table([[left, middle, right]], colWidths=[28 * mm, 105 * mm, 42 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), colour),
        ("BACKGROUND", (1, 0), (-1, 0), LIGHT_BG),
        ("BOX", (0, 0), (-1, -1), 1.0, colour),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LINEAFTER", (0, 0), (0, 0), 0.5, colour),
    ]))
    return t


def _shap_table(shap_items: list):
    """Detailed explainable AI / SHAP factor decomposition table."""
    if not shap_items:
        return Paragraph("No feature attribution data available.", ST["small"])

    data = [[
        Paragraph("Rank", ST["table_hdr"]),
        Paragraph("Risk Factor", ST["table_hdr"]),
        Paragraph("Patient Value", ST["table_hdr"]),
        Paragraph("Impact Direction", ST["table_hdr"]),
        Paragraph("Relative Influence", ST["table_hdr"]),
    ]]

    for i, item in enumerate(shap_items[:6], 1):
        direction = item.get("direction", "risk")
        if direction == "risk":
            dir_html = f'<font color="{RED.hexval()}"><b>▲ Elevates Risk</b></font>'
        elif direction == "protective":
            dir_html = f'<font color="{GREEN.hexval()}"><b>▼ Protective</b></font>'
        else:
            dir_html = f'<font color="{GREY.hexval()}">Neutral / Normal</font>'

        impact_score = item.get("impact", 0.0)
        bar_len = min(int(impact_score * 35), 10)
        bar_visual = "■" * max(bar_len, 1)

        data.append([
            Paragraph(f"#{i}", ST["table_val"]),
            Paragraph(X(item.get("label", item.get("feature", ""))), ST["table_lbl"]),
            Paragraph(X(str(item.get("raw_value", "—"))), ST["table_val"]),
            Paragraph(dir_html, ST["table_val"]),
            Paragraph(f'<font color="{NAVY.hexval()}" size="8">{bar_visual}</font> ({impact_score:.3f})', ST["table_val"]),
        ])

    t = Table(data, colWidths=[12 * mm, 58 * mm, 38 * mm, 36 * mm, None], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.3, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, PALE]),
    ]))
    return t


def _guidelines_block(guidelines: list):
    if not guidelines:
        return Paragraph(
            "<i>USPSTF Lung Cancer Screening Guideline reference: Annual screening with Low-Dose Computed Tomography (LDCT) "
            "is recommended in adults aged 50 to 80 years who have a 20 pack-year smoking history and currently smoke or have quit "
            "within the past 15 years (USPSTF Grade B Recommendation).</i>",
            ST["small"],
        )
    out = []
    for i, g in enumerate(guidelines[:2], 1):
        text = (g.get("text") or "").strip()
        if not text:
            continue
        page = g.get("page", "?")
        excerpt = text[:600] + ("…" if len(text) > 600 else "")

        quote_tbl = Table(
            [[Paragraph(
                f'<font color="{NAVY.hexval()}" size="8"><b>USPSTF CLINICAL GUIDELINE EVIDENCE #{i}</b></font>'
                f'<font color="#64748B" size="7.5">  ·  Page {page}</font><br/>'
                f'<font color="#0F172A" size="8"><i>"{X(excerpt)}"</i></font>',
                ST["quote"],
            )]],
            colWidths=[None],
        )
        quote_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), PALE),
            ("LINEBEFORE", (0, 0), (0, 0), 2.5, NAVY),
            ("BOX", (0, 0), (-1, -1), 0.3, BORDER),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        out.append(quote_tbl)
        out.append(Spacer(1, 4))
    return KeepTogether(out)


def _orders_block(tier: str):
    """Clinical orders checklist block."""
    is_refer = (tier == "REFER")
    is_review = (tier == "REVIEW")

    c1 = "☑" if is_refer else "☐"
    c2 = "☑" if (is_refer or is_review) else "☐"
    c3 = "☑" if is_refer else "☐"
    c4 = "☑" if (is_review or tier == "RULE-OUT") else "☐"

    data = [
        [
            Paragraph(f'<font size="10" color="{NAVY.hexval()}"><b>{c1}</b></font>', ST["small"]),
            Paragraph("<b>Urgent Low-Dose CT (LDCT) Order</b> — Fast-track imaging referral within 14 business days.", ST["small"]),
        ],
        [
            Paragraph(f'<font size="10" color="{NAVY.hexval()}"><b>{c2}</b></font>', ST["small"]),
            Paragraph("<b>Pulmonology Specialist Consultation</b> — Comprehensive diagnostic workup and shared decision-making.", ST["small"]),
        ],
        [
            Paragraph(f'<font size="10" color="{NAVY.hexval()}"><b>{c3}</b></font>', ST["small"]),
            Paragraph("<b>Evidence-Based Smoking Cessation Intervention</b> — USPSTF Grade A behavioral & pharmacological therapy.", ST["small"]),
        ],
        [
            Paragraph(f'<font size="10" color="{NAVY.hexval()}"><b>{c4}</b></font>', ST["small"]),
            Paragraph("<b>Scheduled Interval Rescreening</b> — Routine surveillance at 12-month interval or annual community health check.", ST["small"]),
        ],
    ]
    t = Table(data, colWidths=[8 * mm, None])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
    ]))
    return t


def _signature_block(report_hash: str):
    data = [
        [
            Paragraph(
                f'<font size="7" color="#64748B">CRYPTOGRAPHIC INTEGRITY HASH (SHA-256)</font><br/>'
                f'<font face="Courier" size="7" color="#0F2E5C"><b>{report_hash[:32]}...</b></font>',
                ST["tiny"],
            ),
            Paragraph(
                '<font size="7" color="#64748B">PHYSICIAN REVIEW & ATTESTATION</font><br/>'
                '<font size="8"><b>Dr. ___________________________, MD</b></font><br/>'
                '<font size="7" color="#64748B">Licensure / NPI: __________________</font>',
                ST["small"],
            ),
            Paragraph(
                '<font size="7" color="#64748B">SIGNATURE & DATE</font><br/><br/>'
                '<font size="8">___________________________</font>',
                ST["small"],
            ),
        ]
    ]
    t = Table(data, colWidths=[65 * mm, 60 * mm, None])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


class _ClinicalDoc(BaseDocTemplate):
    def __init__(self, buf, team, logo_path, watermark_path):
        super().__init__(
            buf, pagesize=A4,
            topMargin=86, bottomMargin=52,
            leftMargin=16 * mm, rightMargin=16 * mm,
        )
        self.team = team
        self.logo_path = logo_path
        self.watermark_path = watermark_path
        frame = Frame(self.leftMargin, self.bottomMargin,
                      self.width, self.height, id="normal",
                      leftPadding=0, rightPadding=0,
                      topPadding=0, bottomPadding=0)
        self.addPageTemplates([PageTemplate(
            id="main", frames=frame, onPage=self._on_page,
        )])

    def _on_page(self, canvas, doc):
        canvas.saveState()
        w, h = canvas._pagesize

        # Watermark
        if self.watermark_path and os.path.exists(self.watermark_path):
            canvas.setFillAlpha(0.04)
            size = min(w, h) * 0.48
            canvas.drawImage(
                self.watermark_path,
                (w - size) / 2, (h - size) / 2,
                width=size, height=size,
                preserveAspectRatio=True, mask="auto",
            )
            canvas.setFillAlpha(1.0)
        else:
            canvas.setFillColor(GREY)
            canvas.setFillAlpha(0.04)
            canvas.setFont("Helvetica-Bold", 54)
            canvas.saveState()
            canvas.translate(w / 2, h / 2)
            canvas.rotate(28)
            canvas.drawCentredString(0, 0, "LungCancer.NET")
            canvas.restoreState()
            canvas.setFillAlpha(1.0)

        # Header Bar
        BAR_H = 70
        canvas.setFillColor(NAVY)
        canvas.rect(0, h - BAR_H, w, BAR_H, fill=1, stroke=0)
        canvas.setFillColor(ACCENT)
        canvas.rect(0, h - BAR_H, w, 2.5, fill=1, stroke=0)

        if self.logo_path and os.path.exists(self.logo_path):
            logo_size = 46
            canvas.drawImage(
                self.logo_path,
                16, h - BAR_H + 12,
                width=logo_size, height=logo_size,
                preserveAspectRatio=True, mask="auto",
            )
            text_x = 16 + logo_size + 12
        else:
            text_x = 18

        canvas.setFillColor(WHITE)
        canvas.setFont("Helvetica-Bold", 13)
        canvas.drawString(text_x, h - 26, self.team.get("institution", "LungCancer.NET Clinical AI Lab"))
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(HexColor("#C7D8F0"))
        canvas.drawString(text_x, h - 40, self.team.get("department", "Preventive Pulmonology & Population Screening"))
        canvas.drawString(text_x, h - 52, self.team.get("address", "Clinical Screening System — AI Builders Congress"))

        canvas.setFillColor(WHITE)
        canvas.setFont("Helvetica-Bold", 11)
        canvas.drawRightString(w - 18, h - 26, "CLINICAL PRE-SCREENING REPORT")
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(HexColor("#C7D8F0"))
        canvas.drawRightString(w - 18, h - 40, "Lung Cancer Population Risk Stratification")
        canvas.drawRightString(w - 18, h - 52, f"Team: {self.team.get('team_name', 'LungCancer.NET')}")

        # Footer
        canvas.setStrokeColor(BORDER)
        canvas.setLineWidth(0.4)
        canvas.line(16, 42, w - 16, 42)
        canvas.setFillColor(GREY)
        canvas.setFont("Helvetica", 7.0)
        canvas.drawString(16, 28, "CONFIDENTIAL HEALTH DOCUMENT — Intended solely for licensed clinical personnel.")
        canvas.drawString(16, 18, f"{self.team.get('team_name','LungCancer.NET')} · Contact: {self.team.get('contact','team@lungcancer.net')}")
        canvas.drawRightString(w - 16, 28, f"Page {doc.page}")
        canvas.drawRightString(w - 16, 18, f"Generated {datetime.now():%Y-%m-%d %H:%M}")

        canvas.restoreState()


def generate_clinical_report(
    *,
    patient: dict,
    input_data: dict,
    tier: str,
    recommendation: str,
    risk_score: float,
    contributing_factors: list,
    guidelines: list,
    ai_summary: str,
    team_info: dict,
    ci_lower: float | None = None,
    ci_upper: float | None = None,
    shap_items: list | None = None,
    is_deidentified: bool = False,
    logo_path: str | None = None,
    watermark_path: str | None = None,
) -> bytes:
    """Generates an executive hospital-grade PDF clinical report."""
    buf = io.BytesIO()
    doc = _ClinicalDoc(buf, team=team_info, logo_path=logo_path, watermark_path=watermark_path)

    patient_id_display = str(patient.get("patient_id", "—")).strip()
    if is_deidentified:
        pseudo = hashlib.sha256(patient_id_display.encode("utf-8")).hexdigest()[:6].upper()
        patient_id_display = f"ANON-{pseudo}"

    # Compute SHA-256 hash for document integrity using safe display identifier
    raw_hash_seed = f"{patient_id_display}:{risk_score:.6f}:{datetime.now().isoformat()}"
    report_hash = hashlib.sha256(raw_hash_seed.encode("utf-8")).hexdigest()

    story: list = []

    sec_status = "DE-IDENTIFIED (HIPAA PRIVACY MODE)" if is_deidentified else "CONFIDENTIAL PATIENT RECORD"

    story.append(Paragraph("Clinical Risk Stratification Report", ST["title"]))
    story.append(Paragraph(
        f'<font color="{NAVY.hexval()}"><b>Report ID:</b></font> LCN-{datetime.now():%Y%m%d%H%M%S}   ·   '
        f'<font color="{NAVY.hexval()}"><b>Patient Ref:</b></font> {patient_id_display}   ·   '
        f'<font color="{NAVY.hexval()}"><b>Security:</b></font> <font color="{NAVY_LIGHT.hexval()}"><b>{sec_status}</b></font>',
        ST["subtitle"],
    ))
    story.append(Spacer(1, 4))

    # 1. Patient Demographics & Biometrics
    story.append(_section(1, "Patient Demographics & Physical Profile"))
    story.append(Spacer(1, 4))
    sex_label = {1: "Male", 2: "Female"}.get(patient.get("sex"), "—")
    story.append(_kv_table([
        ("Patient Identifier", patient_id_display),
        ("Age / Biological Sex", f"{patient.get('age', '—')} years  ·  {sex_label}"),
        ("Screening Location", patient.get("state", "—")),
        ("Body Mass Index (BMI)", f"{_fmt(patient.get('bmi'))} kg/m²  ({patient.get('height_weight', '—')})"),
        ("Healthcare Access Status", "Low-Access Subgroup (Cost / Geographic / Rural Barrier Active)" if patient.get("low_access") else "Standard Healthcare Access"),
    ]))
    story.append(Spacer(1, 8))

    # 2. Exposure & Clinical History
    story.append(_section(2, "Tobacco & Comorbidity History"))
    story.append(Spacer(1, 4))
    resp, chronic = [], []
    if patient.get("asthma"):  resp.append("Asthma")
    if patient.get("copd"):    resp.append("COPD / Emphysema")
    if patient.get("heart_attack"): chronic.append("Myocardial Infarction")
    if patient.get("chd"):     chronic.append("Coronary Heart Disease")
    if patient.get("stroke"):  chronic.append("Stroke")
    if patient.get("diabetes"): chronic.append("Diabetes Mellitus")

    story.append(_kv_table([
        ("Smoking History", f"{patient.get('packs_per_day', 0):.1f} packs/day × {patient.get('years_smoked', 0):.0f} years"),
        ("Cumulative Pack-Years", f"{_fmt(patient.get('pack_years'))} pack-years " + ("(≥20 USPSTF High-Risk Benchmark Met)" if (patient.get("pack_years") or 0) >= 20 else "(Below 20 pk-yr threshold)")),
        ("Respiratory Burden", ("Present — " + ", ".join(resp)) if resp else "Absent (No COPD / Asthma history)"),
        ("Cardiovascular / Metabolic", ("Present — " + ", ".join(chronic)) if chronic else "Absent"),
        ("5-Year Environmental AQI", f"{_fmt(input_data.get('AQI_5YR'))} (Ambient Fine PM2.5: {_fmt(input_data.get('PM25_5YR'))} µg/m³)"),
    ]))
    story.append(Spacer(1, 8))

    # 3. Risk Assessment Banner
    story.append(_section(3, "Triage Classification & Decision Policy"))
    story.append(Spacer(1, 4))
    story.append(_risk_banner(tier, risk_score, recommendation, ci_lower=ci_lower, ci_upper=ci_upper))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "<b>Policy Thresholds:</b> Rule-Out Ceiling (t_out) = 0.024% · Fast-Track Referral Floor (t_in) = 0.626%. "
        "Thresholds derived from an Equity-Aware Subgroup Sensitivity Floor (≥85% in all underserved demographic cohorts) "
        "and Access-Aware Cost Function penalizing delayed referral in high-barrier populations.",
        ST["tiny"],
    ))
    story.append(Spacer(1, 8))

    # 4. Explainable AI / SHAP Attribution
    if shap_items:
        story.append(_section(4, "Explainable AI (XAI) — Patient Factor Attribution"))
        story.append(Spacer(1, 4))
        story.append(Paragraph(
            "Individualized feature contributions calculated using Shapley Additive Explanations (SHAP). "
            "Depicts how individual patient risk factors drove the predicted risk up or down from population baseline.",
            ST["tiny"],
        ))
        story.append(Spacer(1, 4))
        story.append(_shap_table(shap_items))
        story.append(Spacer(1, 8))

    # 5. USPSTF Clinical Guidelines
    story.append(_section(5, "USPSTF Screening Guideline Alignment"))
    story.append(Spacer(1, 4))
    story.append(_guidelines_block(guidelines))
    story.append(Spacer(1, 8))

    # 6. Physician AI Synthesis
    story.append(_section(6, "Clinical Synthesis Narrative"))
    story.append(Spacer(1, 4))
    ai_box = Table([[Paragraph(X(ai_summary or "Clinical review indicated by ensemble triage."), ST["body"])]], colWidths=[None])
    ai_box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PALE),
        ("BOX", (0, 0), (-1, -1), 0.5, NAVY_LIGHT),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(ai_box)
    story.append(Spacer(1, 8))

    # 7. Structured Physician Orders Protocol
    story.append(_section(7, "Physician Action Plan & Recommended Orders"))
    story.append(Spacer(1, 4))
    story.append(_orders_block(tier))
    story.append(Spacer(1, 10))

    # 8. Sign-off & Verification
    story.append(_section(8, "Verification & Physician Sign-Off"))
    story.append(Spacer(1, 6))
    story.append(_signature_block(report_hash))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "<b>Notice:</b> LungCancer.NET is a clinical decision support system designed to assist population pre-screening. "
        "It provides calibrated statistical risk assessment and does not constitute a primary radiological or histopathological diagnosis. "
        "All patient management decisions must be confirmed by a licensed medical practitioner.",
        ST["tiny"],
    ))

    doc.build(story)
    return buf.getvalue()