from __future__ import annotations

import calendar
from datetime import date, timedelta
from html import escape
from typing import Any

YEAR = 2027
MAX_PEOPLE_PER_DAY = 5
CALENDAR_MONTHS: list[tuple[int, int]] = [(2027, m) for m in range(1, 13)]

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


def get_month_weeks(year: int, month: int) -> list[tuple[int, list[int | None]]]:
    """Devuelve lista de (num_semana, [lun..dom]) para un mes y año dados."""
    cal = calendar.Calendar(firstweekday=0)  # 0 = Lunes
    weeks_raw = cal.monthdayscalendar(year, month)
    result: list[tuple[int, list[int | None]]] = []
    for week in weeks_raw:
        first_day = next(day for day in week if day != 0)
        week_num = get_custom_week_number(date(year, month, first_day))
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


def _get_day_person_ids(raw_val: Any) -> list[str]:
    if isinstance(raw_val, str) and raw_val:
        return [raw_val]
    if isinstance(raw_val, list):
        return [pid for pid in raw_val if isinstance(pid, str) and pid][:MAX_PEOPLE_PER_DAY]
    return []


def build_legend_html(data: dict[str, Any]) -> str:
    """Genera el HTML de la leyenda con los colores y nombres de las personas."""
    people: dict[str, dict[str, str]] = data.get("people", {})
    days: dict[str, Any] = data.get("days", {})

    counts: dict[str, int] = {}
    for raw_val in days.values():
        for person_id in _get_day_person_ids(raw_val):
            counts[person_id] = counts.get(person_id, 0) + 1

    items_html = [
        '<div class="legend-item">'
        '<span class="legend-swatch holiday-swatch"></span>'
        f'<span class="legend-label"><strong>Feriado / Fecha considerada</strong> ({len(HOLIDAYS)})</span>'
        "</div>"
    ]

    for pid, pinfo in people.items():
        color = escape(pinfo.get("color", "#3B82F6"))
        name = escape(pinfo.get("name", pid))
        count = counts.get(pid, 0)
        suffix = f" ({count} {'día' if count == 1 else 'días'})"
        items_html.append(
            f'<div class="legend-item person-legend" data-pid="{escape(pid)}" data-name="{name}" data-color="{color}" title="Clic derecho para ver solo a {name}">'
            f'<span class="legend-swatch" style="background:{color};"></span>'
            f'<span class="legend-label"><strong>{name}</strong>{suffix}</span>'
            f"</div>"
        )

    if not people:
        items_html.append(
            '<div class="legend-empty">Aún no hay personas registradas. '
            "Agrega una persona y elige un color en el panel izquierdo.</div>"
        )

    return (
        '<div class="legend-box">'
        '<div class="legend-header-row">'
        '<div class="legend-title">LEYENDA DE PERIODOS <span class="legend-hint">(Clic en barrita = ver nombre · Clic derecho = filtrar)</span></div>'
        '<button type="button" id="reset-filter-btn" class="reset-filter-btn" style="display:none;">👥 Visualizar todos</button>'
        '</div>'
        f'<div class="legend-grid">{"".join(items_html)}</div>'
        '</div>'
    )


def build_calendar_html(data: dict[str, Any]) -> str:
    """Genera el HTML completo del calendario 2027 + Enero 2028 (13 meses + leyenda + feriados)."""
    people: dict[str, dict[str, str]] = data.get("people", {})
    days_map: dict[str, Any] = data.get("days", {})

    months_html: list[str] = []
    for yr, m in CALENDAR_MONTHS:
        m_name = MONTH_NAMES[m - 1] if yr == YEAR else f"{MONTH_NAMES[m - 1]} {yr}"
        m_num = f"{m:02d}" if yr == YEAR else f"{m:02d}/{str(yr)[2:]}"
        weeks = get_month_weeks(yr, m)

        rows_html: list[str] = []
        for week_num, cells in weeks:
            td_cells: list[str] = [f'<td class="sem-col">{week_num}</td>']
            for idx, day_num in enumerate(cells):
                if day_num is None:
                    td_cells.append('<td class="day-empty"></td>')
                    continue

                iso = f"{yr}-{m:02d}-{day_num:02d}"
                is_weekend = idx >= 5
                holiday_name = HOLIDAYS.get(iso)
                day_pids = [pid for pid in _get_day_person_ids(days_map.get(iso)) if pid in people]

                classes = ["day-cell"]
                if is_weekend:
                    classes.append("weekend")
                if holiday_name:
                    classes.append("holiday")
                if day_pids:
                    classes.append("has-marks")

                date_label = f"{day_num:02d} {MONTH_ABBR[m-1]} {yr}"
                title_parts: list[str] = [date_label]
                if day_pids:
                    names_str = ", ".join(people[pid].get("name", "") for pid in day_pids)
                    title_parts.append(f"Asignado a: {names_str}")
                if holiday_name:
                    title_parts.append(f"Feriado: {holiday_name}")

                bars_html = "".join(
                    f'<span class="mark-bar" '
                    f'data-pid="{escape(pid)}" '
                    f'data-name="{escape(people[pid].get("name", pid))}" '
                    f'data-color="{escape(people[pid].get("color", "#3B82F6"))}" '
                    f'data-date="{escape(date_label)}" '
                    f'style="background-color:{escape(people[pid].get("color", "#3B82F6"))};"></span>'
                    for pid in day_pids
                )
                marks_html = f'<div class="day-marks">{bars_html}</div>' if bars_html else '<div class="day-marks empty-marks"></div>'

                title_attr = f' title="{escape(" | ".join(title_parts))}"'
                td_cells.append(
                    f'<td class="{" ".join(classes)}"{title_attr}>'
                    f'<div class="day-num">{day_num}</div>{marks_html}'
                    f'</td>'
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

    # Feriados footer (2 columns)
    holiday_items = sorted(HOLIDAYS.items())
    mid_idx = (len(holiday_items) + 1) // 2
    left_col = holiday_items[:mid_idx]
    right_col = holiday_items[mid_idx:]

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

    html = f"""
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
                <span class="hol-count">{len(HOLIDAYS)} fechas</span>
            </div>
            <div class="holidays-cols">
                {render_holiday_list(left_col)}
                {render_holiday_list(right_col)}
            </div>
        </div>
    </div>
    """
    return "\n".join(line.lstrip() for line in html.splitlines() if line.strip())


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
    padding: 2px 1px;
    height: 27px;
    vertical-align: top;
    border-radius: 2px;
}
.month-table td.sem-col {
    text-align: left;
    font-size: 10px;
    color: #9ca3af;
    font-weight: 500;
    vertical-align: middle;
}
.month-table td.day-cell {
    color: #1f2937;
}
.month-table td.day-cell.weekend .day-num {
    font-weight: 700;
}
.month-table td.day-cell.holiday {
    background-color: #fdeaea;
    color: #c0392b;
    border-bottom: 2px solid #c0392b;
}
.month-table td.day-cell.holiday .day-num {
    color: #c0392b;
    font-weight: 700;
}
.day-num {
    line-height: 1.15;
    font-size: 11px;
}
.day-marks {
    display: flex;
    gap: 1px;
    width: 92%;
    margin: 2px auto 0 auto;
    height: 5px;
}
.day-marks.empty-marks {
    visibility: hidden;
}
.mark-bar {
    flex: 1 1 0;
    height: 100%;
    border-radius: 1.5px;
    border: 0.5px solid rgba(0, 0, 0, 0.15);
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

.legend-header-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
    gap: 8px;
}
.legend-hint {
    font-weight: 500;
    color: #9ca3af;
    text-transform: none;
    letter-spacing: 0;
}
.reset-filter-btn {
    background: #1f2937;
    color: #ffffff;
    border: none;
    border-radius: 4px;
    padding: 3px 9px;
    font-size: 11px;
    font-weight: 600;
    cursor: pointer;
}
.reset-filter-btn:hover {
    background: #374151;
}
.person-legend {
    cursor: context-menu;
    padding: 2px 6px;
    border-radius: 4px;
    transition: opacity 0.15s ease, background-color 0.15s ease;
}
.person-legend:hover {
    background-color: #eef2f7;
}
.person-legend.active-filter {
    background-color: #e0e7ff;
    outline: 1.5px solid #4f46e5;
}
.person-legend.dimmed-filter {
    opacity: 0.32;
}
.mark-bar {
    cursor: pointer;
    transition: transform 0.1s ease;
}
.mark-bar:hover {
    transform: scaleY(1.35);
}
.bar-tooltip {
    position: fixed;
    z-index: 9998;
    background: #111827;
    color: #ffffff;
    padding: 6px 10px;
    border-radius: 6px;
    font-size: 12px;
    box-shadow: 0 6px 18px rgba(0, 0, 0, 0.25);
    display: none;
    align-items: center;
    gap: 7px;
    pointer-events: none;
    white-space: nowrap;
}
.bar-tooltip-dot {
    width: 10px;
    height: 10px;
    border-radius: 2px;
    border: 1px solid rgba(255, 255, 255, 0.4);
    flex-shrink: 0;
}
.cal-context-menu {
    position: fixed;
    z-index: 9999;
    background: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.18);
    min-width: 210px;
    padding: 4px;
    display: none;
    font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
}
.cal-ctx-item {
    display: flex;
    align-items: center;
    gap: 8px;
    width: 100%;
    text-align: left;
    background: transparent;
    border: none;
    padding: 7px 10px;
    font-size: 12.5px;
    color: #1f2937;
    border-radius: 4px;
    cursor: pointer;
}
.cal-ctx-item:hover {
    background: #f3f4f6;
}
.cal-ctx-dot {
    width: 10px;
    height: 10px;
    border-radius: 2px;
    display: inline-block;
    flex-shrink: 0;
}

/* Estilos de impresión en Streamlit */
@media print {
    header[data-testid="stHeader"],
    section[data-testid="stSidebar"],
    div[data-testid="stToolbar"],
    div[data-testid="stDecoration"],
    .no-print,
    .legend-hint,
    .reset-filter-btn,
    .bar-tooltip,
    .cal-context-menu {
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


CALENDAR_INTERACTIVE_JS = """
<div id="bar-tooltip" class="bar-tooltip">
    <span id="bar-tooltip-dot" class="bar-tooltip-dot"></span>
    <span id="bar-tooltip-text"></span>
</div>
<div id="cal-context-menu" class="cal-context-menu">
    <button type="button" id="ctx-only-btn" class="cal-ctx-item">
        <span id="ctx-only-dot" class="cal-ctx-dot"></span>
        <span id="ctx-only-label">Visualizar solo seleccionado</span>
    </button>
    <button type="button" id="ctx-all-btn" class="cal-ctx-item">
        <span>👥</span>
        <span>Visualizar todos</span>
    </button>
</div>
<script>
(function() {
    const tooltip = document.getElementById("bar-tooltip");
    const tooltipDot = document.getElementById("bar-tooltip-dot");
    const tooltipText = document.getElementById("bar-tooltip-text");
    const ctxMenu = document.getElementById("cal-context-menu");
    const ctxOnlyBtn = document.getElementById("ctx-only-btn");
    const ctxOnlyDot = document.getElementById("ctx-only-dot");
    const ctxOnlyLabel = document.getElementById("ctx-only-label");
    const ctxAllBtn = document.getElementById("ctx-all-btn");
    const resetBtn = document.getElementById("reset-filter-btn");

    let activeFilterPid = null;
    let contextTarget = null;

    function hideTooltip() {
        tooltip.style.display = "none";
    }

    function hideContextMenu() {
        ctxMenu.style.display = "none";
    }

    function applyFilter(pid) {
        activeFilterPid = pid;
        const bars = document.querySelectorAll(".mark-bar");
        bars.forEach(function(bar) {
            if (!pid || bar.dataset.pid === pid) {
                bar.style.display = "";
            } else {
                bar.style.display = "none";
            }
        });

        const legends = document.querySelectorAll(".person-legend");
        legends.forEach(function(leg) {
            leg.classList.remove("active-filter", "dimmed-filter");
            if (pid) {
                if (leg.dataset.pid === pid) {
                    leg.classList.add("active-filter");
                } else {
                    leg.classList.add("dimmed-filter");
                }
            }
        });

        if (resetBtn) {
            resetBtn.style.display = pid ? "inline-block" : "none";
        }
    }

    function showTooltipForBar(bar, clientX, clientY) {
        const name = bar.dataset.name || "";
        const color = bar.dataset.color || "#3B82F6";
        const dateStr = bar.dataset.date || "";
        tooltipDot.style.backgroundColor = color;
        tooltipText.innerHTML = "<strong>" + name + "</strong>" + (dateStr ? " · " + dateStr : "");
        tooltip.style.display = "flex";

        const rect = tooltip.getBoundingClientRect();
        let left = clientX - rect.width / 2;
        let top = clientY - rect.height - 12;
        if (left < 8) left = 8;
        if (left + rect.width > window.innerWidth - 8) left = window.innerWidth - rect.width - 8;
        if (top < 8) top = clientY + 14;
        tooltip.style.left = left + "px";
        tooltip.style.top = top + "px";
    }

    function showContextMenu(targetEl, clientX, clientY) {
        contextTarget = {
            pid: targetEl.dataset.pid,
            name: targetEl.dataset.name || "seleccionado",
            color: targetEl.dataset.color || "#3B82F6"
        };
        ctxOnlyDot.style.backgroundColor = contextTarget.color;
        ctxOnlyLabel.textContent = "Visualizar solo seleccionado (" + contextTarget.name + ")";
        ctxMenu.style.display = "block";

        const rect = ctxMenu.getBoundingClientRect();
        let left = clientX;
        let top = clientY;
        if (left + rect.width > window.innerWidth - 8) left = window.innerWidth - rect.width - 8;
        if (top + rect.height > window.innerHeight - 8) top = window.innerHeight - rect.height - 8;
        if (left < 8) left = 8;
        if (top < 8) top = 8;
        ctxMenu.style.left = left + "px";
        ctxMenu.style.top = top + "px";
    }

    document.addEventListener("click", function(e) {
        const bar = e.target.closest(".mark-bar");
        hideContextMenu();
        if (bar) {
            e.stopPropagation();
            showTooltipForBar(bar, e.clientX, e.clientY);
        } else {
            hideTooltip();
        }
    });

    document.addEventListener("contextmenu", function(e) {
        const targetEl = e.target.closest(".mark-bar, .person-legend");
        if (targetEl && targetEl.dataset.pid) {
            e.preventDefault();
            hideTooltip();
            showContextMenu(targetEl, e.clientX, e.clientY);
        } else {
            hideContextMenu();
        }
    });

    document.addEventListener("keydown", function(e) {
        if (e.key === "Escape") {
            hideTooltip();
            hideContextMenu();
        }
    });

    if (ctxOnlyBtn) {
        ctxOnlyBtn.addEventListener("click", function(e) {
            e.stopPropagation();
            if (contextTarget && contextTarget.pid) {
                applyFilter(contextTarget.pid);
            }
            hideContextMenu();
        });
    }

    if (ctxAllBtn) {
        ctxAllBtn.addEventListener("click", function(e) {
            e.stopPropagation();
            applyFilter(null);
            hideContextMenu();
        });
    }

    if (resetBtn) {
        resetBtn.addEventListener("click", function(e) {
            e.stopPropagation();
            applyFilter(null);
        });
    }
})();
</script>
"""


def build_interactive_document(data: dict[str, Any]) -> str:
    """Genera el documento HTML interactivo para embeber en Streamlit."""
    cal_html = build_calendar_html(data)
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
{CALENDAR_CSS}
<style>
html, body {{
    margin: 0;
    padding: 0;
    background: transparent;
    font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
}}
</style>
</head>
<body>
{cal_html}
{CALENDAR_INTERACTIVE_JS}
</body>
</html>
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
        height: 21px;
        padding: 1px 1px;
    }}
    .day-num {{
        font-size: 9.5px;
    }}
    .day-marks {{
        height: 4px;
        margin-top: 1px;
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
{CALENDAR_INTERACTIVE_JS}
</body>
</html>
"""
