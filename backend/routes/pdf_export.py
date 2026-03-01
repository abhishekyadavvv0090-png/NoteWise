from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
import io
from datetime import datetime

router = APIRouter()

class PDFExportRequest(BaseModel):
    video_title: str
    channel: str
    url: str
    duration: int
    notes: list[dict]  # [{timestamp, timestamp_label, content, type}]

def format_duration(seconds: int) -> str:
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"

@router.post("/export")
async def export_pdf(request: PDFExportRequest):
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )

        # Colors
        primary = HexColor('#0F0F0F')
        accent = HexColor('#F5A623')
        secondary = HexColor('#1A1A2E')
        text_primary = HexColor('#1A1A1A')
        text_secondary = HexColor('#555555')
        ai_note_bg = HexColor('#F8F9FF')
        user_note_bg = HexColor('#FFF8F0')
        border_color = HexColor('#E0E0E0')

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=22,
            fontName='Helvetica-Bold',
            textColor=text_primary,
            spaceAfter=6,
            leading=28
        )

        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Normal'],
            fontSize=11,
            fontName='Helvetica',
            textColor=text_secondary,
            spaceAfter=4
        )

        section_header_style = ParagraphStyle(
            'SectionHeader',
            parent=styles['Normal'],
            fontSize=13,
            fontName='Helvetica-Bold',
            textColor=text_primary,
            spaceBefore=16,
            spaceAfter=8
        )

        timestamp_style = ParagraphStyle(
            'Timestamp',
            parent=styles['Normal'],
            fontSize=9,
            fontName='Helvetica-Bold',
            textColor=accent,
            spaceAfter=2
        )

        note_style = ParagraphStyle(
            'Note',
            parent=styles['Normal'],
            fontSize=10.5,
            fontName='Helvetica',
            textColor=text_primary,
            leading=16,
            spaceAfter=4
        )

        meta_style = ParagraphStyle(
            'Meta',
            parent=styles['Normal'],
            fontSize=9,
            fontName='Helvetica',
            textColor=text_secondary,
            spaceAfter=2
        )

        story = []

        # Header banner using Table
        now = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        header_data = [[
            Paragraph('<font color="white" size="16"><b>NoteWise</b></font>', styles['Normal']),
            Paragraph(f'<font color="#AAAAAA" size="8">Generated {now}</font>', styles['Normal'])
        ]]
        header_table = Table(header_data, colWidths=[10*cm, 7*cm])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), primary),
            ('PADDING', (0, 0), (-1, -1), 14),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 16))

        # Video title
        safe_title = request.video_title.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        story.append(Paragraph(safe_title, title_style))

        # Video metadata
        story.append(Paragraph(f"📺  Channel: <b>{request.channel}</b>", subtitle_style))
        story.append(Paragraph(f"⏱  Duration: <b>{format_duration(request.duration)}</b>", subtitle_style))
        safe_url = request.url.replace('&', '&amp;')
        story.append(Paragraph(f"🔗  <a href='{safe_url}' color='#0066CC'>{safe_url}</a>", subtitle_style))

        story.append(Spacer(1, 8))
        story.append(HRFlowable(width="100%", thickness=2, color=accent, spaceAfter=16))

        # Notes count summary
        ai_notes = [n for n in request.notes if n.get('type') != 'user']
        user_notes = [n for n in request.notes if n.get('type') == 'user']

        summary_data = [[
            Paragraph(f'<b>{len(request.notes)}</b><br/><font size="8" color="#555555">Total Notes</font>', styles['Normal']),
            Paragraph(f'<b>{len(ai_notes)}</b><br/><font size="8" color="#555555">AI Generated</font>', styles['Normal']),
            Paragraph(f'<b>{len(user_notes)}</b><br/><font size="8" color="#555555">User Added</font>', styles['Normal']),
        ]]
        summary_table = Table(summary_data, colWidths=[5.67*cm, 5.67*cm, 5.67*cm])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#F5F5F5')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 12),
            ('FONTSIZE', (0, 0), (-1, -1), 16),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, 0), (-1, -1), text_primary),
            ('BOX', (0, 0), (-1, -1), 1, border_color),
            ('LINEAFTER', (0, 0), (1, 0), 1, border_color),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 20))

        # Notes section
        story.append(Paragraph("📝  Notes", section_header_style))
        story.append(HRFlowable(width="100%", thickness=1, color=border_color, spaceAfter=10))

        # Sort notes by timestamp
        sorted_notes = sorted(request.notes, key=lambda x: x.get('timestamp', 0))

        for i, note in enumerate(sorted_notes):
            is_user_note = note.get('type') == 'user'
            ts_label = note.get('timestamp_label', '00:00')
            content = note.get('content', '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            note_type_label = "👤 Custom Note" if is_user_note else "🤖 AI Note"
            bg_color = user_note_bg if is_user_note else ai_note_bg

            note_data = [[
                Paragraph(f'<font color="#F5A623"><b>[{ts_label}]</b></font>  <font size="8" color="#888888">{note_type_label}</font>', note_style),
            ], [
                Paragraph(content, note_style),
            ]]

            note_table = Table(note_data, colWidths=[16.67*cm])
            note_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), bg_color),
                ('PADDING', (0, 0), (-1, -1), 10),
                ('BOX', (0, 0), (-1, -1), 0.5, border_color),
                ('TOPPADDING', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, -1), (-1, -1), 10),
                ('LINEBEFORE', (0, 0), (0, -1), 3, accent if is_user_note else HexColor('#4A90E2')),
            ]))

            story.append(note_table)
            story.append(Spacer(1, 6))

        # Footer
        story.append(Spacer(1, 20))
        story.append(HRFlowable(width="100%", thickness=1, color=border_color))
        story.append(Spacer(1, 8))
        story.append(Paragraph(
            '<font size="8" color="#888888">Generated by NoteWise · AI-Powered YouTube Note-Taking</font>',
            ParagraphStyle('Footer', parent=styles['Normal'], alignment=TA_CENTER)
        ))

        doc.build(story)
        buffer.seek(0)

        safe_filename = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in request.video_title)[:50]
        filename = f"NoteWise_{safe_filename}.pdf"

        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")
