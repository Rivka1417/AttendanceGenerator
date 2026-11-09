from pathlib import Path
from typing import Callable
from src.domain.models import AttendanceReport
from src.domain.enums import ReportType
from src.generation.base_renderer import BaseRenderer


class HtmlRenderer(BaseRenderer):
    def __init__(self, output_dir: str = "output"):
        super().__init__(output_dir)
        self._formatters = {
            ReportType.TYPE_A: self._format_type_a,
            ReportType.TYPE_B: self._format_type_b
        }

    def render(self, report: AttendanceReport, original_filename: str) -> Path:
        output_path = self._get_output_filename(original_filename, "html")
        formatter = self._formatters.get(report.report_type)

        if not formatter:
            raise ValueError(f"HTML format not supported for {report.report_type}")

        table_html, summary_html = formatter(report)

        html_content = f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>דו"ח נוכחות מעודכן - {report.employee_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 30px; background-color: #f4f6f9; color: #333; }}
        h1 {{ color: #2c3e50; border-bottom: 2px solid #34495e; padding-bottom: 10px; }}
        h2 {{ color: #34495e; font-size: 18px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; background: #fff; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        th, td {{ border: 1px solid #dcdde1; padding: 10px 12px; text-align: center; font-size: 14px; }}
        th {{ background-color: #2f3640; color: #fff; }}
        tr:nth-child(even) {{ background-color: #f8f9fa; }}
        .summary {{ margin-top: 25px; background: #f1f2f6; padding: 20px; border-radius: 6px; border: 1px solid #dfe4ea; }}
        .summary h3 {{ margin-top: 0; color: #2f3640; }}
        .summary p {{ margin: 6px 0; font-size: 15px; }}
    </style>
</head>
<body>
    <h1>דו"ח נוכחות מבוקר ומעודכן</h1>
    <h2>חברה: {report.company_name} | עובד: {report.employee_name} (ת.ז: {report.employee_id})</h2>
    <table>
        {table_html}
    </table>
    <div class="summary">
        <h3>סיכום נתונים חודשי</h3>
        {summary_html}
    </div>
</body>
</html>
"""
        output_path.write_text(html_content, encoding="utf-8")
        return output_path

    def _format_type_a(self, report: AttendanceReport) -> tuple[str, str]:
        table = """<thead>
            <tr>
                <th>תאריך</th><th>יום</th><th>מיקום</th><th>כניסה</th><th>יציאה</th>
                <th>סה"כ</th><th>הפסקה</th><th>100%</th><th>125%</th><th>150%</th><th>שבת</th>
            </tr>
        </thead>
        <tbody>\n"""
        for r in report.rows:
            table += f"<tr><td>{r.date}</td><td>{r.day_of_week}</td><td>{getattr(r, 'location', '-')}</td><td>{r.entry_time or '-'}</td><td>{r.exit_time or '-'}</td><td>{r.total_hours}</td><td>{r.break_time or '-'}</td><td>{r.hours_100}</td><td>{r.hours_125}</td><td>{r.hours_150}</td><td>{r.shabbat_hours}</td></tr>\n"
        table += "</tbody>"

        summary = f"""<p><strong>סה"כ ימים:</strong> {report.summary.total_days}</p>
        <p><strong>שעות חודשיות:</strong> {report.summary.total_monthly_hours}</p>
        <p><strong>100%:</strong> {report.summary.total_100} | <strong>125%:</strong> {report.summary.total_125} | <strong>150%:</strong> {report.summary.total_150}</p>
        <p><strong>בונוס:</strong> {report.summary.bonus} | <strong>נסיעות:</strong> {report.summary.travel_expenses}</p>"""
        return table, summary

    def _format_type_b(self, report: AttendanceReport) -> tuple[str, str]:
        table = """<thead>
            <tr><th>תאריך</th><th>יום</th><th>כניסה</th><th>יציאה</th><th>סה"כ שעות</th><th>הערות</th></tr>
        </thead>
        <tbody>\n"""
        for r in report.rows:
            table += f"<tr><td>{r.date}</td><td>{r.day_of_week}</td><td>{r.entry_time or '-'}</td><td>{r.exit_time or '-'}</td><td>{r.total_hours}</td><td>{getattr(r, 'notes', '') or ''}</td></tr>\n"
        table += "</tbody>"

        summary = f"""<p><strong>סה"כ ימים:</strong> {report.summary.total_days}</p>
        <p><strong>שעות חודשיות:</strong> {report.summary.total_monthly_hours}</p>
        <p><strong>מחיר לשעה:</strong> {report.summary.hourly_rate} ₪</p>
        <p><strong>סה"כ לתשלום:</strong> {report.summary.total_payment} ₪</p>"""
        return table, summary