#!/usr/bin/env python3
"""
Niessbrauch-Szenario-Rechner

Simuliert die Anlage der jährlichen Mieteinnahmen eines Kindes in:
A) Tagesgeld
B) ETF
C) Kombination aus Tagesgeld + ETF

- Berücksichtigt Inflation
- Zeigt nominale und reale (inflationsbereinigte) Werte
- Schöne, übersichtliche Konsolenausgabe
"""

from dataclasses import dataclass
from typing import List, Optional


# =========================
#   KONFIGURATION (DEFAULTS)
# =========================

DEFAULT_DEPOSIT_YEARS = 11      # Jahre MIT Mieteinnahmen
DEFAULT_GROWTH_YEARS = 5        # Jahre OHNE Mieteinnahmen (nur Wachstum)
DEFAULT_ANNUAL_DEPOSIT = 10_200 # jährlicher Netto-Betrag für das Kind
DEFAULT_TG_RATE = 0.02          # Tagesgeldzins (2 %)
DEFAULT_ETF_RATE = 0.05         # ETF-Rendite (5 % -> anpassbar)
DEFAULT_INFLATION = 0.02        # Inflation (2 %)

# Kombi-Strategie:
DEFAULT_TG_TARGET_FIRST = 5_000     # Tagesgeld-Ziel der ersten Phase
DEFAULT_TG_TARGET_AFTER = 10_000    # Tagesgeld-Ziel ab Phase 2
DEFAULT_YEARS_FIRST_TARGET = 3      # Jahre mit erstem TG-Ziel


# =========================
#   DATENSTRUKTUREN
# =========================

@dataclass
class YearResult:
    year: int
    deposit: float
    tg_balance: float
    etf_balance: float
    total_nominal: float
    total_real: float


# =========================
#   HILFSFUNKTIONEN
# =========================

def real_value(nominal: float, inflation_rate: float, year: int) -> float:
    """Berechnet den inflationsbereinigten Wert (heutige Kaufkraft)."""
    return nominal / ((1 + inflation_rate) ** year)


def format_money(value: float) -> str:
    """Formatiert Geldbeträge schön mit Tausenderpunkt und 2 Nachkommastellen."""
    return f"{value:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def print_header(title: str) -> None:
    print("\n" + "=" * 80)
    print(title.center(80))
    print("=" * 80)


def print_table(results: List[YearResult], inflation_rate: float, scenario_name: str) -> None:
    print_header(f"Szenario: {scenario_name}")
    header = f"{'Jahr':>4} | {'Einzahlung':>12} | {'TG-Stand':>12} | {'ETF-Stand':>12} | {'Gesamt':>12} | {'Real (heute)':>14}"
    print(header)
    print("-" * len(header))

    for r in results:
        print(
            f"{r.year:>4} | "
            f"{format_money(r.deposit):>12} | "
            f"{format_money(r.tg_balance):>12} | "
            f"{format_money(r.etf_balance):>12} | "
            f"{format_money(r.total_nominal):>12} | "
            f"{format_money(r.total_real):>14}"
        )

    total_deposits = sum(r.deposit for r in results)
    final_nominal = results[-1].total_nominal
    final_real = results[-1].total_real

    print("-" * len(header))
    print(f"{'Summe Einzahlungen:':<20} {format_money(total_deposits)}")
    print(f"{'Endstand nominal:':<20} {format_money(final_nominal)}")
    print(f"{'Endstand real:':<20} {format_money(final_real)}")
    print(f"{'Inflation p.a.:':<20} {inflation_rate*100:.2f} %")
    print()


# =========================
#   SIMULATIONEN
# =========================

def simulate_tagesgeld(
    deposit_years: int,
    growth_years: int,
    annual_deposit: float,
    tg_rate: float,
    inflation_rate: float,
) -> List[YearResult]:
    results: List[YearResult] = []
    tg_balance = 0.0
    total_years = deposit_years + growth_years

    for year in range(1, total_years + 1):
        # Einzahlung nur in der Mieteinnahmen-Phase
        deposit = annual_deposit if year <= deposit_years else 0.0
        tg_balance = (tg_balance + deposit) * (1 + tg_rate)
        total_nominal = tg_balance
        total_real = real_value(total_nominal, inflation_rate, year)
        results.append(
            YearResult(
                year=year,
                deposit=deposit,
                tg_balance=tg_balance,
                etf_balance=0.0,
                total_nominal=total_nominal,
                total_real=total_real,
            )
        )
    return results


def simulate_etf(
    deposit_years: int,
    growth_years: int,
    annual_deposit: float,
    etf_rate: float,
    inflation_rate: float,
) -> List[YearResult]:
    results: List[YearResult] = []
    etf_balance = 0.0
    total_years = deposit_years + growth_years

    for year in range(1, total_years + 1):
        # Einzahlung nur in der Mieteinnahmen-Phase
        deposit = annual_deposit if year <= deposit_years else 0.0
        etf_balance = (etf_balance + deposit) * (1 + etf_rate)
        total_nominal = etf_balance
        total_real = real_value(total_nominal, inflation_rate, year)
        results.append(
            YearResult(
                year=year,
                deposit=deposit,
                tg_balance=0.0,
                etf_balance=etf_balance,
                total_nominal=total_nominal,
                total_real=total_real,
            )
        )
    return results


def simulate_combo(
    deposit_years: int,
    growth_years: int,
    annual_deposit: float,
    tg_rate: float,
    etf_rate: float,
    inflation_rate: float,
    tg_target_first: float,
    tg_target_after: float,
    years_first_target: int,
) -> List[YearResult]:
    """
    Kombi-Strategie:
    - Zuerst wird Tagesgeld bis zum Zielbetrag (tg_target_first / tg_target_after) aufgefüllt.
    - Alles, was darüber hinausgeht, wird im jeweiligen Jahr in den ETF gesteckt.
    - Nach der Einzahlungsphase wächst das Geld weiter (nur Zinsen/Rendite).
    """
    results: List[YearResult] = []
    tg_balance = 0.0
    etf_balance = 0.0
    total_years = deposit_years + growth_years

    for year in range(1, total_years + 1):
        # Ziel für das Tagesgeld in diesem Jahr
        target = tg_target_first if year <= years_first_target else tg_target_after

        # Einzahlung nur in der Mieteinnahmen-Phase
        deposit = annual_deposit if year <= deposit_years else 0.0
        remaining = deposit

        # Zuerst Tagesgeld bis zur Zielgröße auffüllen
        if tg_balance < target and remaining > 0:
            needed = target - tg_balance
            alloc = min(remaining, needed)
            tg_balance += alloc
            remaining -= alloc

        # Rest geht in ETF
        etf_balance += remaining

        # Verzinsung / Wertentwicklung am Jahresende
        tg_balance *= (1 + tg_rate)
        etf_balance *= (1 + etf_rate)

        # Überschuss vom Tagesgeld in ETF umschichten
        if tg_balance > target:
            excess = tg_balance - target
            etf_balance += excess
            tg_balance = target

        total_nominal = tg_balance + etf_balance
        total_real = real_value(total_nominal, inflation_rate, year)

        results.append(
            YearResult(
                year=year,
                deposit=deposit,
                tg_balance=tg_balance,
                etf_balance=etf_balance,
                total_nominal=total_nominal,
                total_real=total_real,
            )
        )
    return results


# =========================
#   INTERAKTIVE ABFRAGE
# =========================

def ask_float(prompt: str, default: float) -> float:
    text = input(f"{prompt} [{default}]: ").strip()
    if not text:
        return default
    return float(text.replace(",", "."))


def ask_int(prompt: str, default: int) -> int:
    text = input(f"{prompt} [{default}]: ").strip()
    if not text:
        return default
    return int(text)


def main():
    print_header("Nießbrauch-Szenario-Rechner – Mieteinnahmen des Kindes")

    deposit_years = ask_int("Jahre MIT Mieteinnahmen", DEFAULT_DEPOSIT_YEARS)
    growth_years = ask_int("Weitere Jahre OHNE Mieteinnahmen (nur Wachstum)", DEFAULT_GROWTH_YEARS)
    annual_deposit = ask_float("Jährliche Einzahlung (Netto Mieteinnahmen des Kindes)", DEFAULT_ANNUAL_DEPOSIT)
    tg_rate = ask_float("Zinssatz Tagesgeld (z. B. 0.02 = 2 %)", DEFAULT_TG_RATE)
    etf_rate = ask_float("Rendite ETF (z. B. 0.05 = 5 %)", DEFAULT_ETF_RATE)
    inflation_rate = ask_float("Inflation (z. B. 0.02 = 2 %)", DEFAULT_INFLATION)

    print("\nKombi-Strategie (Tagesgeld + ETF):")
    tg_target_first = ask_float("TG-Ziel in Phase 1 (z. B. 5000)", DEFAULT_TG_TARGET_FIRST)
    years_first_target = ask_int("Anzahl Jahre mit TG-Ziel Phase 1", DEFAULT_YEARS_FIRST_TARGET)
    tg_target_after = ask_float("TG-Ziel ab Phase 2 (z. B. 10000)", DEFAULT_TG_TARGET_AFTER)

    # Simulationen
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

    # Ausgabe
    print_table(res_tg, inflation_rate, "A) Nur Tagesgeld")
    print_table(res_etf, inflation_rate, "B) Nur ETF")
    print_table(res_combo, inflation_rate, "C) Kombination Tagesgeld + ETF")

    print("Hinweis: 'Real (heute)' berücksichtigt die eingegebene Inflationsrate.")
    print("Du kannst das Skript beliebig oft mit anderen Parametern starten, um Szenarien zu vergleichen.")


if __name__ == "__main__":
    main()