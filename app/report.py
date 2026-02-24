import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
import json

def generate_pdf_report(scan_data, output_path):
    """
    Generates a professional forensic PDF report using reportlab.
    scan_data is the SQLAlchemy model instance representing the scan.
    """
    doc = SimpleDocTemplate(output_path, pagesize=letter,
                            rightMargin=40, leftMargin=40,
                            topMargin=40, bottomMargin=40)
    
    styles = getSampleStyleSheet()
    
    # Custom Styles for TruthGuard Brand
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=28, textColor=colors.HexColor("#0A84FF"), spaceAfter=5, alignment=1, fontName="Helvetica-Bold")
    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=12, textColor=colors.HexColor("#64748b"), spaceAfter=30, alignment=1)
    
    h2_style = ParagraphStyle('Heading2', parent=styles['Heading2'], fontSize=16, textColor=colors.HexColor("#0f172a"), spaceBefore=20, spaceAfter=10, fontName="Helvetica-Bold")
    h3_style = ParagraphStyle('Heading3', parent=styles['Heading3'], fontSize=13, textColor=colors.HexColor("#334155"), spaceBefore=15, spaceAfter=8, fontName="Helvetica-Bold")
    
    normal_style = ParagraphStyle('NormalText', parent=styles['Normal'], fontSize=11, textColor=colors.HexColor("#334155"), leading=16)
    bold_style = ParagraphStyle('BoldText', parent=normal_style, fontName="Helvetica-Bold")
    
    alert_style = ParagraphStyle('AlertText', parent=normal_style, textColor=colors.HexColor("#ef4444"))
    success_style = ParagraphStyle('SuccessText', parent=normal_style, textColor=colors.HexColor("#10b981"))

    elements = []
    
    # ================= HEADERS =================
    elements.append(Paragraph("<b>TRUTHGUARD AI</b>", title_style))
    elements.append(Paragraph("OFFICIAL FORENSIC ANALYSIS REPORT", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#0A84FF"), spaceAfter=20, spaceBefore=0))
    
    # Load detailed JSON from db
    try:
        details = json.loads(scan_data.details_json)
    except:
        details = {}

    # ================= EXECUTIVE SUMMARY =================
    verdict_color = colors.HexColor("#ef4444") if scan_data.verdict == "FAKE" else colors.HexColor("#10b981")
    probability_str = f"{int(scan_data.fake_probability * 100)}%"
    
    exec_data = [
        ["REPORT IDENTIFIER:", scan_data.scan_id, "DATE OF ANALYSIS:", scan_data.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")],
        ["TARGET MEDIA:", scan_data.filename, "PROCESSING TIME:", details.get('processing_time', 'N/A')],
        ["MANIPULATION PROB:", Paragraph(f"<b>{probability_str}</b>", normal_style), "FINAL VERDICT:", Paragraph(f"<b><font color='{verdict_color}' size='12'>{scan_data.verdict}</font></b>", normal_style)]
    ]
    
    exec_table = Table(exec_data, colWidths=[130, 150, 130, 110])
    exec_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor("#1e293b")),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTNAME', (1,0), (1,-1), 'Helvetica'),
        ('FONTNAME', (3,0), (3,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1"))
    ]))
    
    elements.append(exec_table)
    elements.append(Spacer(1, 20))
    
    # ================= CONCLUSION =================
    elements.append(Paragraph("EXECUTIVE CONCLUSION", h2_style))
    explanation = details.get("explanation", "No detailed explanation available.")
    elements.append(Paragraph(explanation, normal_style))
    elements.append(Spacer(1, 15))

    # ================= INTEGRITY BREAKDOWN =================
    elements.append(Paragraph("COMPONENT INTEGRITY SCORES", h2_style))
    
    component_data = [["MEDIA COMPONENT", "REALNESS CONFIDENCE", "STATUS"]]
    comps = details.get("components", {})
    
    for comp_name, comp_value in comps.items():
        if comp_value == "N/A":
            status = "Not Analyzed"
            status_color = colors.HexColor("#94a3b8")
        else:
            try:
                val = float(comp_value)
                if val < 50:
                    status = "HIGH RISK"
                    status_color = colors.HexColor("#ef4444")
                elif val < 80:
                    status = "MODERATE RISK"
                    status_color = colors.HexColor("#f59e0b")
                else:
                    status = "AUTHENTIC"
                    status_color = colors.HexColor("#10b981")
            except:
                status = "Unknown"
                status_color = colors.HexColor("#94a3b8")
                
        val_str = f"{comp_value}%" if comp_value != "N/A" else "N/A"
        component_data.append([
            comp_name.upper(), 
            val_str, 
            Paragraph(f"<b><font color='{status_color}'>{status}</font></b>", normal_style)
        ])
        
    comp_table = Table(component_data, colWidths=[173, 173, 174])
    comp_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0f172a")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('TOPPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#f1f5f9")),
        ('GRID', (0,0), (-1,-1), 1, colors.white),
        ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1"))
    ]))
    
    elements.append(comp_table)
    elements.append(Spacer(1, 20))

    # ================= DETAILED FORENSIC FINDINGS =================
    elements.append(Paragraph("DETAILED FORENSIC MODULE FINDINGS", h2_style))
    checks = details.get("checks", {})
    
    for check_key, check_data in checks.items():
        title = f"{check_key.upper()} ANALYSIS"
        passed = check_data.get("pass", False)
        status_text = "PASS (Authentic)" if passed else "FAIL (Synthetic/Manipulated)"
        status_style = success_style if passed else alert_style
        
        elements.append(Paragraph(title, h3_style))
        elements.append(Paragraph(f"<b>Status:</b> <font color='{status_style.textColor}'>{status_text}</font>", normal_style))
        elements.append(Paragraph(f"<b>Detail:</b> {check_data.get('detail', 'N/A')}", normal_style))
        
        report_data = check_data.get('report', {})
        if report_data:
            report_str = []
            for k, v in report_data.items():
                if isinstance(v, (list, dict)): continue  # Skip complex objects
                report_str.append(f"<b>{str(k).replace('_', ' ').capitalize()}:</b> {v}")
            
            if report_str:
                elements.append(Paragraph(" | ".join(report_str), normal_style))
        
        elements.append(Spacer(1, 10))
        
    elements.append(Spacer(1, 20))
    
    # ================= DISCLAIMER =================
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=15))
    disclaimer = "This report was generated automatically by TruthGuard AI. While the models utilize state-of-the-art multimodal deep learning fusion (CNN boundaries, ELA artifacts, Audio Spectra analysis), results are probabilistic and should not be used as the sole basis for critical legal or journalistic decisions without human expert validation."
    elements.append(Paragraph(f"<i>Disclaimer: {disclaimer}</i>", ParagraphStyle('Small', parent=normal_style, fontSize=8, textColor=colors.HexColor("#64748b"))))
    
    # Build Document
    doc.build(elements)
    
    return output_path
