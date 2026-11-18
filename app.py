from __future__ import annotations

import calendar
import re
from datetime import date, timedelta
from typing import Any

import streamlit as st

from calendar_data import (
    CALENDAR_CSS,
    MONTH_NAMES,
    PRESET_COLORS,
    YEAR,
    build_calendar_html,
    build_printable_document,
)
from storage import is_github_persistence_enabled, load_data, update_data

st.set_page_config(
    page_title="Calendario 2027 - Southern Perú",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(CALENDAR_CSS, unsafe_allow_html=True)


def _slugify(name: str) -> str:
    clean = re.sub(r"\s+", " ", name.strip().lower())
    slug = re.sub(r"[^a-z0-9áéíóúñü]+", "-", clean).strip("-")
    return slug or "persona"


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
        if st.button("🔄 Actualizar", use_container_width=True, help="Cargar los últimos cambios guardados por otras personas"):
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

    # 2. Marcar periodos o días
    st.subheader("2. Marcar Periodo / Días")

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

        tab_rango, tab_dias = st.tabs(["📆 Por Periodo", "🔢 Días sueltos"])

        with tab_rango:
            d_start = st.date_input(
                "Desde",
                value=date(YEAR, 1, 1),
                min_value=date(YEAR, 1, 1),
                max_value=date(YEAR, 12, 31),
                format="DD/MM/YYYY",
            )
            d_end = st.date_input(
                "Hasta",
                value=date(YEAR, 1, 7),
                min_value=date(YEAR, 1, 1),
                max_value=date(YEAR, 12, 31),
                format="DD/MM/YYYY",
            )

            c1, c2 = st.columns(2)
            with c1:
                mark_range = st.button("✅ Marcar", use_container_width=True, type="primary")
            with c2:
                clear_range = st.button("🧹 Limpiar", use_container_width=True)

            if mark_range or clear_range:
                if d_end < d_start:
                    st.warning("La fecha 'Hasta' debe ser igual o posterior a 'Desde'.")
                else:
                    target_dates: list[str] = []
                    cur = d_start
                    while cur <= d_end:
                        target_dates.append(cur.isoformat())
                        cur += timedelta(days=1)

                    def _apply_range(d: dict[str, Any]) -> None:
                        for iso in target_dates:
                            if mark_range:
                                d["days"][iso] = selected_pid
                            else:
                                d["days"].pop(iso, None)

                    action_txt = f"Marcar {len(target_dates)} días ({sel_name})" if mark_range else f"Limpiar {len(target_dates)} días"
                    try:
                        st.session_state["cal_data"] = update_data(_apply_range, commit_message=action_txt)
                        st.toast(action_txt, icon="✅" if mark_range else "🧹")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Error al guardar: {exc}")

        with tab_dias:
            sel_month_idx = st.selectbox(
                "Mes",
                options=list(range(1, 13)),
                format_func=lambda m: f"{m:02d} - {MONTH_NAMES[m - 1]}",
            )
            max_day = calendar.monthrange(YEAR, sel_month_idx)[1]
            sel_days = st.multiselect(
                "Días del mes",
                options=list(range(1, max_day + 1)),
                placeholder="Elige uno o más días",
            )
            c3, c4 = st.columns(2)
            with c3:
                mark_days = st.button("✅ Aplicar", key="btn_mark_days", use_container_width=True, type="primary")
            with c4:
                clear_days = st.button("🧹 Quitar", key="btn_clear_days", use_container_width=True)

            if (mark_days or clear_days) and sel_days:
                iso_list = [f"{YEAR}-{sel_month_idx:02d}-{day:02d}" for day in sel_days]

                def _apply_days(d: dict[str, Any]) -> None:
                    for iso in iso_list:
                        if mark_days:
                            d["days"][iso] = selected_pid
                        else:
                            d["days"].pop(iso, None)

                action_txt = f"Actualizar {len(iso_list)} días de {MONTH_NAMES[sel_month_idx - 1]}"
                try:
                    st.session_state["cal_data"] = update_data(_apply_days, commit_message=action_txt)
                    st.toast(action_txt, icon="✅" if mark_days else "🧹")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Error al guardar: {exc}")

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
                    d["days"] = {k: v for k, v in d["days"].items() if v != del_pid}

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
# MAIN: Calendario 2027 + Leyenda + Feriados
# ---------------------------------------------------------------------------
st.markdown(build_calendar_html(st.session_state["cal_data"]), unsafe_allow_html=True)
