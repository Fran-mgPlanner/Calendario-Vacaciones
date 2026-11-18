from __future__ import annotations

import calendar
from datetime import date, timedelta
from html import escape
from typing import Any

YEAR = 2027

MONTH_NAMES = [
    "ENERO",
    "FEBRERO",
    "MARZO",
    "ABRIL",
    "MAYO",
    "JUNIO",
    "JULIO",
    "AGOSTO",
    "SEPTIEMBRE",
    "OCTUBRE",
    "NOVIEMBRE",
    "DICIEMBRE",
]

MONTH_ABBR = [
    "ENE", "FEB", "MAR", "ABR", "MAY", "JUN",
    "JUL", "AGO", "SEP", "OCT", "NOV", "DIC",
]

# Week 3335 starts on Monday 2026-12-28 (which contains 2027-01-01).
BASE_MONDAY = date(2026, 12, 28)
BASE_WEEK_NUM = 3335

# 18 feriados y fechas consideradas del calendario 2027
HOLIDAYS: dict[str, str] = {
    "2027-01-01": "Año Nuevo",
    "2027-03-25": "Jueves Santo",
    "2027-03-26": "Viernes Santo",
    "2027-05-01": "Día del Trabajo",
    "2027-06-07": "Batalla de Arica y Día de la Bandera",
    "2027-06-29": "San Pedro y San Pablo",
    "2027-07-23": "Día de la Fuerza Aérea del Perú",
    "2027-07-28": "Fiestas Patrias - Independencia del Perú",
    "2027-07-29": "Fiestas Patrias",
    "2027-08-06": "Batalla de Junín",
    "2027-08-28": "Día de Tacna",
    "2027-08-30": "Santa Rosa de Lima",
    "2027-10-08": "Combate de Angamos",
    "2027-11-01": "Todos los Santos",
    "2027-12-05": "Día del Minero",
    "2027-12-08": "Inmaculada Concepción",
    "2027-12-09": "Batalla de Ayacucho",
    "2027-12-25": "Navidad",
}

PRESET_COLORS = [
    "#3B82F6",  # Azul
    "#10B981",  # Verde Esmeralda
    "#F59E0B",  # Ámbar
    "#8B5CF6",  # Violeta
    "#EC4899",  # Rosa
    "#06B6D4",  # Cian
    "#F97316",  # Naranja
    "#84CC16",  # Lima
    "#6366F1",  # Índigo
    "#14B8A6",  # Turquesa
]


def get_custom_week_number(d: date) -> int:
    """Devuelve el número de semana corporativo (3335 para la semana del 1 de enero 2027)."""
    monday = d - timedelta(days=d.weekday())
    return BASE_WEEK_NUM + ((monday - BASE_MONDAY).days // 7)


def get_month_weeks(month: int) -> list[tuple[int, list[int | None]]]:
    """Devuelve lista de (num_semana, [lun..dom]) para un mes de 2027."""
    cal = calendar.Calendar(firstweekday=0)  # 0 = Lunes
    weeks_raw = cal.monthdayscalendar(YEAR, month)
    result: list[tuple[int, list[int | None]]] = []
    for week in weeks_raw:
        first_day = next(day for day in week if day != 0)
        week_num = get_custom_week_number(date(YEAR, month, first_day))
        cells = [day if day != 0 else None for day in week]
        result.append((week_num, cells))
    return result


def get_contrast_text_color(hex_color: str) -> str:
    """Elige texto oscuro o claro según la luminosidad del color de fondo."""
    hex_clean = hex_color.lstrip("#")
    if len(hex_clean) != 6:
        return "#111827"
    r, g, b = int(hex_clean[0:2], 16), int(hex_clean[2:4], 16), int(hex_clean[4:6], 16)
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return "#FFFFFF" if luminance < 0.58 else "#111827"


def build_legend_html(data: dict[str, Any]) -> str:
    """Genera el HTML de la leyenda con los colores y nombres de las personas."""
    people: dict[str, dict[str, str]] = data.get("people", {})
    days: dict[str, str] = data.get("days", {})

    counts: dict[str, int] = {}
    for person_id in days.values():
        counts[person_id] = counts.get(person_id, 0) + 1

    items_html = [
        '<div class="legend-item">'
        '<span class="legend-swatch holiday-swatch"></span>'
        '<span class="legend-label"><strong>Feriado / Fecha considerada</strong> (18)</span>'
        "</div>"
    ]

    for pid, pinfo in people.items():
        color = escape(pinfo.get("color", "#3B82F6"))
        name = escape(pinfo.get("name", pid))
        count = counts.get(pid, 0)
        suffix = f" ({count} {'día' if count == 1 else 'días'})"
        items_html.append(
            f'<div class="legend-item">'
            f'<span class="legend-swatch" style="background:{color};"></span>'
            f'<span class="legend-label"><strong>{name}</strong>{suffix}</span>'
            f"</div>"
        )

    if not people:
        items_html.append(
            '<div class="legend-empty">Aún no hay personas registradas. '
            "Agrega una persona y elige un color en el panel izquierdo.</div>"
        )

    return f'<div class="legend-box"><div class="legend-title">LEYENDA DE PERIODOS</div><div class="legend-grid">{"".join(items_html)}</div></div>'


def build_calendar_html(data: dict[str, Any]) -> str:
    """Genera el HTML completo del calendario 2027 (12 meses + leyenda + feriados)."""
    people: dict[str, dict[str, str]] = data.get("people", {})
    days_map: dict[str, str] = data.get("days", {})

    months_html: list[str] = []
    for m in range(1, 13):
        m_name = MONTH_NAMES[m - 1]
        m_num = f"{m:02d}"
        weeks = get_month_weeks(m)

        rows_html: list[str] = []
        for week_num, cells in weeks:
            td_cells: list[str] = [f'<td class="sem-col">{week_num}</td>']
            for idx, day_num in enumerate(cells):
                if day_num is None:
                    td_cells.append('<td class="day-empty"></td>')
                    continue

                iso = f"{YEAR}-{m:02d}-{day_num:02d}"
                is_weekend = idx >= 5
                holiday_name = HOLIDAYS.get(iso)
                person_id = days_map.get(iso)
                person = people.get(person_id) if person_id else None

                classes = ["day-cell"]
                if is_weekend:
                    classes.append("weekend")
                if holiday_name:
                    classes.append("holiday")

                style_parts: list[str] = []
                title_parts: list[str] = [f"{day_num:02d} {MONTH_ABBR[m-1]} {YEAR}"]

                if person:
                    bg = person.get("color", "#3B82F6")
                    fg = get_contrast_text_color(bg)
                    style_parts.append(f"background-color:{escape(bg)};color:{fg};font-weight:700;")
                    title_parts.append(f"Asignado a: {person.get('name', '')}")
                if holiday_name:
                    title_parts.append(f"Feriado: {holiday_name}")

                style_attr = f' style="{"".join(style_parts)}"' if style_parts else ""
                title_attr = f' title="{escape(" | ".join(title_parts))}"'
                td_cells.append(
                    f'<td class="{" ".join(classes)}"{style_attr}{title_attr}>{day_num}</td>'
                )

            rows_html.append(f'<tr>{"".join(td_cells)}</tr>')

        months_html.append(
            f"""
            <div class="month-card">
                <div class="month-header">
                    <span class="month-name">{m_name}</span>
                    <span class="month-num">{m_num}</span>
                </div>
                <table class="month-table">
                    <thead>
                        <tr>
                            <th class="sem-head">SEM.</th>
                            <th>LU</th><th>MA</th><th>MI</th><th>JU</th><th>VI</th>
                            <th class="wknd-head">SÁ</th><th class="wknd-head">DO</th>
                        </tr>
                    </thead>
                    <tbody>
                        {"".join(rows_html)}
                    </tbody>
                </table>
            </div>
            """
        )

    # Feriados footer (2 columns, 9 items each)
    holiday_items = sorted(HOLIDAYS.items())
    left_col = holiday_items[:9]
    right_col = holiday_items[9:]

    def render_holiday_list(items: list[tuple[str, str]]) -> str:
        lis = []
        for iso, desc in items:
            _, mm, dd = iso.split("-")
            label = f"{dd} {MONTH_ABBR[int(mm) - 1]}"
            lis.append(
                f'<li><span class="hol-date">{label}</span>'
                f'<span class="hol-desc">{escape(desc)}</span></li>'
            )
        return f'<ul class="hol-list">{"".join(lis)}</ul>'

    legend_html = build_legend_html(data)

    return f"""
    <div id="printable-calendar" class="cal-wrapper">
        <div class="cal-top-header">
            <div>
                <div class="cal-kicker">CALENDARIO</div>
                <div class="cal-year">2027</div>
                <div class="cal-subtitle">Mantenimiento Planeamiento Mina / Gerencia Concentradora</div>
            </div>
            <div class="cal-brand">
                <div class="brand-main">Southern Perú</div>
                <div class="brand-sub">Grupo México · MINERÍA</div>
            </div>
        </div>

        {legend_html}

        <div class="months-grid">
            {"".join(months_html)}
        </div>

        <div class="holidays-footer">
            <div class="holidays-title">
                <span><span class="hol-bar"></span> FERIADOS Y FECHAS CONSIDERADAS</span>
                <span class="hol-count">18 fechas</span>
            </div>
            <div class="holidays-cols">
                {render_holiday_list(left_col)}
                {render_holiday_list(right_col)}
            </div>
        </div>
    </div>
    """


CALENDAR_CSS = """
<style>
.cal-wrapper {
    font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    background: #ffffff;
    color: #1f2937;
    padding: 18px 20px;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    max-width: 1080px;
    margin: 0 auto;
}
.cal-top-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    border-bottom: 2px solid #d1d5db;
    padding-bottom: 8px;
    margin-bottom: 12px;
}
.cal-kicker {
    font-size: 11px;
    font-weight: 700;
    color: #c0392b;
    letter-spacing: 0.8px;
}
.cal-year {
    font-size: 38px;
    font-weight: 800;
    line-height: 1;
    color: #1f2937;
}
.cal-subtitle {
    font-size: 13px;
    font-weight: 700;
    color: #374151;
    margin-top: 2px;
}
.cal-brand {
    text-align: right;
}
.brand-main {
    font-size: 20px;
    font-weight: 700;
    color: #374151;
}
.brand-sub {
    font-size: 11px;
    font-weight: 600;
    color: #6b7280;
}

/* Leyenda */
.legend-box {
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    padding: 8px 12px;
    margin-bottom: 14px;
}
.legend-title {
    font-size: 10px;
    font-weight: 700;
    color: #6b7280;
    letter-spacing: 0.6px;
    margin-bottom: 6px;
}
.legend-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 8px 18px;
    align-items: center;
}
.legend-item {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    color: #1f2937;
}
.legend-swatch {
    width: 14px;
    height: 14px;
    border-radius: 3px;
    display: inline-block;
    border: 1px solid rgba(0,0,0,0.18);
    flex-shrink: 0;
}
.holiday-swatch {
    background: #fdeaea;
    border-bottom: 2px solid #c0392b;
}
.legend-empty {
    font-size: 12px;
    color: #6b7280;
    font-style: italic;
}

/* 12-month grid */
.months-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 14px 18px;
}
@media (max-width: 900px) {
    .months-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}
@media (max-width: 600px) {
    .months-grid {
        grid-template-columns: 1fr;
    }
}
.month-card {
    break-inside: avoid;
}
.month-header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    border-bottom: 1.5px solid #4b5563;
    padding-bottom: 2px;
    margin-bottom: 4px;
}
.month-name {
    font-size: 13px;
    font-weight: 800;
    color: #1f2937;
    letter-spacing: 0.3px;
}
.month-num {
    font-size: 11px;
    font-weight: 700;
    color: #6b7280;
}
.month-table {
    width: 100%;
    border-collapse: collapse;
    table-layout: fixed;
    font-size: 11.5px;
}
.month-table th {
    font-size: 9.5px;
    font-weight: 600;
    color: #6b7280;
    padding: 3px 1px;
    text-align: center;
    border-bottom: 1px solid #e5e7eb;
}
.month-table th.sem-head {
    text-align: left;
    color: #9ca3af;
    width: 34px;
}
.month-table th.wknd-head {
    font-weight: 800;
    color: #374151;
}
.month-table td {
    text-align: center;
    padding: 3px 1px;
    height: 22px;
    border-radius: 2px;
}
.month-table td.sem-col {
    text-align: left;
    font-size: 10px;
    color: #9ca3af;
    font-weight: 500;
}
.month-table td.day-cell {
    color: #1f2937;
}
.month-table td.day-cell.weekend {
    font-weight: 700;
}
.month-table td.day-cell.holiday {
    background-color: #fdeaea;
    color: #c0392b;
    font-weight: 700;
    border-bottom: 2px solid #c0392b;
}

/* Feriados footer */
.holidays-footer {
    margin-top: 14px;
    padding-top: 8px;
    border-top: 1.5px solid #d1d5db;
    break-inside: avoid;
}
.holidays-title {
    display: flex;
    justify-content: space-between;
    font-size: 10.5px;
    font-weight: 800;
    color: #1f2937;
    margin-bottom: 6px;
}
.hol-bar {
    display: inline-block;
    width: 14px;
    height: 3px;
    background: #c0392b;
    vertical-align: middle;
    margin-right: 4px;
}
.hol-count {
    font-weight: 500;
    color: #6b7280;
}
.holidays-cols {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
}
.hol-list {
    list-style: none;
    margin: 0;
    padding: 0;
    font-size: 10.5px;
}
.hol-list li {
    display: flex;
    gap: 10px;
    padding: 1.5px 0;
}
.hol-date {
    color: #c0392b;
    font-weight: 700;
    min-width: 46px;
}
.hol-desc {
    color: #374151;
}

/* Estilos de impresión en Streamlit */
@media print {
    header[data-testid="stHeader"],
    section[data-testid="stSidebar"],
    div[data-testid="stToolbar"],
    div[data-testid="stDecoration"],
    .no-print {
        display: none !important;
    }
    .main .block-container {
        padding: 0 !important;
        max-width: 100% !important;
    }
    .cal-wrapper {
        border: none !important;
        padding: 0 !important;
        -webkit-print-color-adjust: exact !important;
        print-color-adjust: exact !important;
    }
    .months-grid {
        grid-template-columns: repeat(3, 1fr) !important;
        gap: 8px 12px !important;
    }
}
</style>
"""


def build_printable_document(data: dict[str, Any]) -> str:
    """Genera un documento HTML autónomo optimizado para imprimir en 1 página."""
    cal_html = build_calendar_html(data)
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Calendario 2027 - Imprimible</title>
{CALENDAR_CSS}
<style>
@page {{
    size: A4 portrait;
    margin: 8mm;
}}
body {{
    margin: 0;
    padding: 12px;
    background: #f3f4f6;
    font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
}}
.print-bar {{
    max-width: 1080px;
    margin: 0 auto 10px auto;
    display: flex;
    justify-content: flex-end;
    gap: 10px;
}}
.print-btn {{
    background: #c0392b;
    color: #fff;
    border: none;
    padding: 8px 16px;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
}}
.print-btn:hover {{
    background: #a93226;
}}
@media print {{
    body {{
        background: #fff;
        padding: 0;
    }}
    .print-bar {{
        display: none !important;
    }}
    .cal-wrapper {{
        border: none;
        padding: 0;
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
    }}
    .cal-year {{
        font-size: 28px;
    }}
    .months-grid {{
        gap: 6px 10px;
    }}
    .month-table td {{
        height: 17px;
        padding: 1.5px 1px;
        font-size: 10px;
    }}
    .legend-box {{
        padding: 5px 8px;
        margin-bottom: 8px;
    }}
    .holidays-footer {{
        margin-top: 8px;
        padding-top: 5px;
    }}
    .hol-list {{
        font-size: 9px;
    }}
}}
</style>
</head>
<body>
<div class="print-bar">
    <button class="print-btn" onclick="window.print()">🖨️ Imprimir / Guardar como PDF</button>
</div>
{cal_html}
</body>
</html>
"""
