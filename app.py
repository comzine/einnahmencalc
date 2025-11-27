"""
Nießbrauch-Szenario-Rechner – Streamlit Web-App
"""

import streamlit as st
import pandas as pd
from main import (
    simulate_tagesgeld,
    simulate_etf,
    simulate_combo,
    DEFAULT_DEPOSIT_YEARS,
    DEFAULT_GROWTH_YEARS,
    DEFAULT_ANNUAL_DEPOSIT,
    DEFAULT_TG_RATE,
    DEFAULT_ETF_RATE,
    DEFAULT_INFLATION,
    DEFAULT_TG_TARGET_FIRST,
    DEFAULT_TG_TARGET_AFTER,
    DEFAULT_YEARS_FIRST_TARGET,
)

st.set_page_config(
    page_title="Nießbrauch-Rechner",
    page_icon="💰",
    layout="wide",
)

st.title("Nießbrauch-Szenario-Rechner")
st.markdown("Simuliert die Anlage der jährlichen Mieteinnahmen eines Kindes")

# Sidebar für Eingaben
with st.sidebar:
    st.header("Parameter")

    st.subheader("Zeitraum")
    deposit_years = st.number_input(
        "Jahre MIT Mieteinnahmen",
        min_value=1,
        max_value=50,
        value=DEFAULT_DEPOSIT_YEARS,
    )
    growth_years = st.number_input(
        "Weitere Jahre OHNE Mieteinnahmen",
        min_value=0,
        max_value=50,
        value=DEFAULT_GROWTH_YEARS,
    )

    st.subheader("Beträge & Zinsen")
    annual_deposit = st.number_input(
        "Jährliche Mieteinnahmen (€)",
        min_value=0,
        max_value=100_000,
        value=DEFAULT_ANNUAL_DEPOSIT,
        step=100,
    )
    tg_rate = st.slider(
        "Tagesgeldzins (%)",
        min_value=0.0,
        max_value=10.0,
        value=DEFAULT_TG_RATE * 100,
        step=0.1,
    ) / 100
    etf_rate = st.slider(
        "ETF-Rendite (%)",
        min_value=0.0,
        max_value=15.0,
        value=DEFAULT_ETF_RATE * 100,
        step=0.1,
    ) / 100
    inflation_rate = st.slider(
        "Inflation (%)",
        min_value=0.0,
        max_value=10.0,
        value=DEFAULT_INFLATION * 100,
        step=0.1,
    ) / 100

    st.subheader("Kombi-Strategie")
    tg_target_first = st.number_input(
        "TG-Ziel Phase 1 (€)",
        min_value=0,
        max_value=50_000,
        value=DEFAULT_TG_TARGET_FIRST,
        step=500,
    )
    years_first_target = st.number_input(
        "Jahre mit TG-Ziel Phase 1",
        min_value=1,
        max_value=20,
        value=DEFAULT_YEARS_FIRST_TARGET,
    )
    tg_target_after = st.number_input(
        "TG-Ziel ab Phase 2 (€)",
        min_value=0,
        max_value=50_000,
        value=DEFAULT_TG_TARGET_AFTER,
        step=500,
    )


def format_euro(value: float) -> str:
    """Formatiert Beträge im deutschen Format."""
    return f"{value:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def results_to_dataframe(results) -> pd.DataFrame:
    """Konvertiert Simulationsergebnisse zu DataFrame."""
    return pd.DataFrame([
        {
            "Jahr": r.year,
            "Einzahlung": format_euro(r.deposit),
            "TG-Stand": format_euro(r.tg_balance),
            "ETF-Stand": format_euro(r.etf_balance),
            "Gesamt": format_euro(r.total_nominal),
            "Real (heute)": format_euro(r.total_real),
        }
        for r in results
    ])


# Simulationen ausführen
res_tg = simulate_tagesgeld(deposit_years, growth_years, annual_deposit, tg_rate, inflation_rate)
res_etf = simulate_etf(deposit_years, growth_years, annual_deposit, etf_rate, inflation_rate)
res_combo = simulate_combo(
    deposit_years,
    growth_years,
    annual_deposit,
    tg_rate,
    etf_rate,
    inflation_rate,
    tg_target_first,
    tg_target_after,
    years_first_target,
)

# Tabs für die drei Szenarien
tab1, tab2, tab3, tab4 = st.tabs(["Nur Tagesgeld", "Nur ETF", "Kombi (TG + ETF)", "Vergleich"])

with tab1:
    st.subheader("Szenario A: Nur Tagesgeld")
    df_tg = results_to_dataframe(res_tg)
    st.dataframe(df_tg, use_container_width=True, hide_index=True)

with tab2:
    st.subheader("Szenario B: Nur ETF")
    df_etf = results_to_dataframe(res_etf)
    st.dataframe(df_etf, use_container_width=True, hide_index=True)

with tab3:
    st.subheader("Szenario C: Kombination Tagesgeld + ETF")
    df_combo = results_to_dataframe(res_combo)
    st.dataframe(df_combo, use_container_width=True, hide_index=True)

with tab4:
    st.subheader("Vergleich der Endstände")

    final_tg = res_tg[-1].total_nominal
    final_etf = res_etf[-1].total_nominal
    final_combo = res_combo[-1].total_nominal

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Tagesgeld", f"{final_tg:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."))
    with col2:
        st.metric("ETF", f"{final_etf:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."))
    with col3:
        st.metric("Kombi", f"{final_combo:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."))

    # Liniendiagramm
    st.line_chart(
        pd.DataFrame({
            "Jahr": [r.year for r in res_tg],
            "Tagesgeld": [r.total_nominal for r in res_tg],
            "ETF": [r.total_nominal for r in res_etf],
            "Kombi": [r.total_nominal for r in res_combo],
        }).set_index("Jahr")
    )

st.caption("Hinweis: 'Real (heute)' berücksichtigt die eingegebene Inflationsrate.")
