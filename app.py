from __future__ import annotations

import calendar
import re
from datetime import date, timedelta
from typing import Any

import streamlit as st
import streamlit.components.v1 as components

from calendar_data import (
    CALENDAR_MONTHS,
    MAX_PEOPLE_PER_DAY,
    MONTH_NAMES,
    PRESET_COLORS,
    YEAR,
    build_interactive_document,
    build_printable_document,
)
from storage import is_github_persistence_enabled, load_data, update_data

st.set_page_config(
    page_title="Calendario 2027 - Southern Perú",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded",
)

# (El CSS y JS del calendario viven dentro de build_interactive_document)

MONTH_NAMES_TITLE = [m.capitalize() for m in MONTH_NAMES]


def _slugify(name: str) -> str:
    clean = re.sub(r"\s+", " ", name.strip().lower())
    slug = re.sub(r"[^a-z0-9áéíóúñü]+", "-", clean).strip("-")
    return slug or "persona"


def _spanish_date_selector(label: str, key_prefix: str, default_month: int = 1, default_day: int = 1) -> date:
    """Selector de fecha (2027 - Ene 2028) con nombres de meses 100% en español."""
    st.caption(label)
    c_mes, c_dia = st.columns([1.8, 1])
    with c_mes:
        yr, month = st.selectbox(
            "Mes",
            options=CALENDAR_MONTHS,
            index=default_month - 1,
            format_func=lambda ym: f"{MONTH_NAMES_TITLE[ym[1] - 1]} {ym[0]}",
            key=f"{key_prefix}_m",
            label_visibility="collapsed",
        )
    max_day = calendar.monthrange(yr, month)[1]
    prev_day = st.session_state.get(f"{key_prefix}_d", default_day)
    safe_day = min(prev_day, max_day)
    with c_dia:
        day = st.selectbox(
            "Día",
            options=list(range(1, max_day + 1)),
            index=safe_day - 1,
            key=f"{key_prefix}_d",
            label_visibility="collapsed",
        )
    return date(yr, month, day)


def _format_spanish_date(d: date) -> str:
    return f"{d.day:02d} de {MONTH_NAMES_TITLE[d.month - 1]} de {d.year}"


def _apply_dates_change(
    target_dates: list[str],
    selected_pid: str,
    sel_name: str,
    is_mark: bool,
) -> None:
    """Marca o quita días para la persona activa (máximo 3 personas por día)."""
    skipped_full = 0

    def _mutate(d: dict[str, Any]) -> None:
        nonlocal skipped_full
        days_dict: dict[str, Any] = d.setdefault("days", {})
        for iso in target_dates:
            raw = days_dict.get(iso, [])
            if isinstance(raw, str):
                cur_list = [raw] if raw else []
            elif isinstance(raw, list):
                cur_list = [x for x in raw if isinstance(x, str) and x]
            else:
                cur_list = []

            if is_mark:
                if selected_pid in cur_list:
                    continue
                if len(cur_list) >= MAX_PEOPLE_PER_DAY:
                    skipped_full += 1
                    continue
                cur_list.append(selected_pid)
                days_dict[iso] = cur_list
            else:
                if selected_pid in cur_list:
                    cur_list = [x for x in cur_list if x != selected_pid]
                if cur_list:
                    days_dict[iso] = cur_list
                else:
                    days_dict.pop(iso, None)

    action_txt = (
        f"Marcar {len(target_dates)} días ({sel_name})"
        if is_mark
        else f"Quitar {len(target_dates)} días ({sel_name})"
    )
    try:
        st.session_state["cal_data"] = update_data(_mutate, commit_message=action_txt)
        if skipped_full > 0:
            st.warning(
                f"Se omitieron {skipped_full} día(s) porque ya tenían el máximo de {MAX_PEOPLE_PER_DAY} personas asignadas."
            )
        st.toast(action_txt, icon="✅" if is_mark else "🧹")
        st.rerun()
    except Exception as exc:
        st.error(f"Error al guardar: {exc}")


def _load_fresh() -> dict[str, Any]:
    try:
        data = load_data()
        st.session_state["cal_data"] = data
        return data
    except Exception as exc:
        st.error(f"Error al cargar datos: {exc}")
        return st.session_state.get("cal_data", {"people": {}, "days": {}})


if "cal_data" not in st.session_state:
    _load_fresh()

data: dict[str, Any] = st.session_state["cal_data"]
people: dict[str, dict[str, str]] = data.get("people", {})

# ---------------------------------------------------------------------------
# SIDEBAR: Controles sencillos para colaborar, guardar e imprimir
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("📅 Calendario 2027")

    col_sync, col_mode = st.columns([1.2, 1])
    with col_sync:
        if st.button(
            "🔄 Actualizar",
            use_container_width=True,
            help="Cargar los últimos cambios guardados por otras personas",
        ):
            data = _load_fresh()
            people = data.get("people", {})
            st.toast("Calendario actualizado", icon="🔄")
    with col_mode:
        if is_github_persistence_enabled():
            st.caption("☁️ GitHub Sync")
        else:
            st.caption("💾 Modo Local")

    st.divider()

    # 1. Registrar persona y color
    st.subheader("1. Persona y Color")
    default_color = PRESET_COLORS[len(people) % len(PRESET_COLORS)]

    with st.form("add_person_form", clear_on_submit=True):
        person_name = st.text_input("Nombre de la persona", placeholder="Ej. Juan Pérez")
        person_color = st.color_picker("Color para la leyenda", value=default_color)
        submitted_person = st.form_submit_button("➕ Agregar / Actualizar", use_container_width=True)

    if submitted_person:
        clean_name = person_name.strip()
        if not clean_name:
            st.warning("Escribe un nombre primero.")
        else:
            pid = _slugify(clean_name)

            def _add_person(d: dict[str, Any]) -> None:
                d["people"][pid] = {"name": clean_name, "color": person_color}

            try:
                st.session_state["cal_data"] = update_data(
                    _add_person, commit_message=f"Persona: {clean_name}"
                )
                st.session_state["active_person"] = pid
                st.toast(f"Guardado: {clean_name}", icon="✅")
                st.rerun()
            except Exception as exc:
                st.error(f"No se pudo guardar: {exc}")

    # 2. Marcar periodos
    st.subheader("2. Marcar Periodo")
    st.caption(f"Hasta **{MAX_PEOPLE_PER_DAY} personas** pueden coincidir en un mismo día.")

    if not people:
        st.info("Agrega al menos una persona arriba para comenzar a marcar días.")
    else:
        person_ids = list(people.keys())
        default_idx = 0
        if st.session_state.get("active_person") in person_ids:
            default_idx = person_ids.index(st.session_state["active_person"])

        selected_pid = st.selectbox(
            "Persona activa",
            options=person_ids,
            index=default_idx,
            format_func=lambda pid: people[pid]["name"],
        )
        st.session_state["active_person"] = selected_pid
        sel_color = people[selected_pid]["color"]
        sel_name = people[selected_pid]["name"]
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">'
            f'<span style="width:16px;height:16px;border-radius:3px;background:{sel_color};display:inline-block;border:1px solid #999;"></span>'
            f'<span style="font-size:13px;">Color activo de <b>{sel_name}</b></span></div>',
            unsafe_allow_html=True,
        )

        tab_rango, tab_inicio = st.tabs(["📆 Por Periodo", "📅 Por Fecha de Inicio"])

        with tab_rango:
            d_start = _spanish_date_selector("Fecha de inicio", "rng_start", default_month=1, default_day=1)
            d_end = _spanish_date_selector("Fecha de fin", "rng_end", default_month=1, default_day=7)

            c1, c2 = st.columns(2)
            with c1:
                mark_range = st.button("✅ Marcar", key="btn_mark_rng", use_container_width=True, type="primary")
            with c2:
                clear_range = st.button("🧹 Quitar", key="btn_clear_rng", use_container_width=True)

            if mark_range or clear_range:
                if d_end < d_start:
                    st.warning("La fecha de fin debe ser igual o posterior a la fecha de inicio.")
                else:
                    target_dates: list[str] = []
                    cur = d_start
                    while cur <= d_end:
                        target_dates.append(cur.isoformat())
                        cur += timedelta(days=1)
                    _apply_dates_change(target_dates, selected_pid, sel_name, is_mark=mark_range)

        with tab_inicio:
            d_ini = _spanish_date_selector("Fecha de inicio", "ini_start", default_month=1, default_day=1)
            cant_dias = int(
                st.number_input(
                    "Cantidad de días (incluyendo el inicio)",
                    min_value=1,
                    max_value=365,
                    value=7,
                    step=1,
                )
            )
            d_calc_end = min(d_ini + timedelta(days=cant_dias - 1), date(YEAR, 12, 31))
            st.caption(f"Del **{d_ini.day:02d}/{d_ini.month:02d}** al **{_format_spanish_date(d_calc_end)}**")

            c3, c4 = st.columns(2)
            with c3:
                mark_ini = st.button("✅ Marcar", key="btn_mark_ini", use_container_width=True, type="primary")
            with c4:
                clear_ini = st.button("🧹 Quitar", key="btn_clear_ini", use_container_width=True)

            if mark_ini or clear_ini:
                target_dates = []
                cur = d_ini
                while cur <= d_calc_end:
                    target_dates.append(cur.isoformat())
                    cur += timedelta(days=1)
                _apply_dates_change(target_dates, selected_pid, sel_name, is_mark=mark_ini)

        with st.expander("⚙️ Administrar personas"):
            del_pid = st.selectbox(
                "Eliminar persona",
                options=person_ids,
                format_func=lambda pid: people[pid]["name"],
                key="del_person_select",
            )
            if st.button("🗑️ Eliminar persona y sus días", use_container_width=True):
                removed_name = people[del_pid]["name"]

                def _remove_person(d: dict[str, Any]) -> None:
                    d["people"].pop(del_pid, None)
                    new_days: dict[str, list[str]] = {}
                    for k, v in d.get("days", {}).items():
                        lst = [v] if isinstance(v, str) else list(v) if isinstance(v, list) else []
                        filtered = [x for x in lst if x != del_pid]
                        if filtered:
                            new_days[k] = filtered
                    d["days"] = new_days

                try:
                    st.session_state["cal_data"] = update_data(
                        _remove_person, commit_message=f"Eliminar persona: {removed_name}"
                    )
                    st.toast(f"Eliminado: {removed_name}", icon="🗑️")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Error al eliminar: {exc}")

    st.divider()

    # 3. Imprimir
    st.subheader("3. Imprimir")
    printable_html = build_printable_document(st.session_state["cal_data"])
    st.download_button(
        label="🖨️ Descargar Vista Imprimible (HTML)",
        data=printable_html.encode("utf-8"),
        file_name="Calendario_2027_Imprimible.html",
        mime="text/html",
        use_container_width=True,
        help="Abre el archivo descargado en tu navegador y presiona el botón Imprimir o Ctrl+P.",
    )
    st.caption("Tip: También puedes presionar **Ctrl + P** directamente en esta página.")

# ---------------------------------------------------------------------------
# MAIN: Calendario 2027 interactivo + Leyenda + Feriados
# ---------------------------------------------------------------------------
components.html(
    build_interactive_document(st.session_state["cal_data"]),
    height=1180,
    scrolling=True,
)
