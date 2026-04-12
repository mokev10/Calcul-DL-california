#!/usr/bin/env python3
"""
driver_license_final_fixed.py
-----------------------------

Application Streamlit principale.
- Lie le menu "Code postal" au menu "Ville"
- Synchronisation bidirectionnelle ZIP <-> Ville
- Affichage automatique du Field Office selon la ville
"""

from __future__ import annotations

import datetime
import hashlib
import random
from typing import Dict, List

import streamlit as st

from california_zip_city import (
    CALIFORNIA_ZIP_TO_CITY,
    find_zips_by_city,
    get_city_from_zip,
)

st.set_page_config(page_title="Permis CA", layout="wide")


# -------------------------
# Données métiers
# -------------------------
FIELD_OFFICES: Dict[str, str] = {
    "Corte Madera": "Baie de San Francisco — Corte Madera (525)",
    "Daly City": "Baie de San Francisco — Daly City (599)",
    "El Cerrito": "Baie de San Francisco — El Cerrito (585)",
    "Fremont": "Baie de San Francisco — Fremont (643)",
    "Hayward": "Baie de San Francisco — Hayward (521)",
    "Novato": "Baie de San Francisco — Novato (647)",
    "Oakland": "Baie de San Francisco — Oakland (501)",
    "Pleasanton": "Baie de San Francisco — Pleasanton (639)",
    "Redwood City": "Baie de San Francisco — Redwood City (542)",
    "San Francisco": "Baie de San Francisco — San Francisco (503)",
    "San Jose": "Baie de San Francisco — San Jose (516)",
    "San Mateo": "Baie de San Francisco — San Mateo (594)",
    "Santa Clara": "Baie de San Francisco — Santa Clara (632)",
    "Vallejo": "Baie de San Francisco — Vallejo (538)",
    "Los Angeles": "Grand Los Angeles — Los Angeles (502)",
    "Culver City": "Grand Los Angeles — Culver City (514)",
    "Glendale": "Grand Los Angeles — Glendale (540)",
    "Hollywood": "Grand Los Angeles — Hollywood (633)",
    "Inglewood": "Grand Los Angeles — Inglewood (544)",
    "Long Beach": "Grand Los Angeles — Long Beach (507)",
    "Pasadena": "Grand Los Angeles — Pasadena (510)",
    "Santa Monica": "Grand Los Angeles — Santa Monica (548)",
    "Torrance": "Grand Los Angeles — Torrance (592)",
    "West Covina": "Grand Los Angeles — West Covina (591)",
    "Costa Mesa": "Orange County / Sud — Costa Mesa (627)",
    "Fullerton": "Orange County / Sud — Fullerton (547)",
    "Laguna Hills": "Orange County / Sud — Laguna Hills (642)",
    "Santa Ana": "Orange County / Sud — Santa Ana (529)",
    "San Clemente": "Orange County / Sud — San Clemente (652)",
    "Westminster": "Orange County / Sud — Westminster (623)",
    "Bakersfield": "Vallée Centrale — Bakersfield (511)",
    "Fresno": "Vallée Centrale — Fresno (505)",
    "Modesto": "Vallée Centrale — Modesto (536)",
    "Stockton": "Vallée Centrale — Stockton (517)",
    "Visalia": "Vallée Centrale — Visalia (519)",
    "Sacramento": "Vallée Centrale — Sacramento (505)",
    "San Diego": "Sud Californie — San Diego (707)",
    "Anaheim": "Orange County / Sud — Anaheim (547)",
    "Irvine": "Orange County / Sud — Irvine (642)",
    "Berkeley": "Baie de San Francisco — Berkeley (585)",
    "Alameda": "Baie de San Francisco — Alameda (501)",
    "Cupertino": "Baie de San Francisco — Cupertino (632)",
}


# -------------------------
# Helpers
# -------------------------
def _city_options() -> List[str]:
    return sorted(set(c for c in CALIFORNIA_ZIP_TO_CITY.values() if c.strip()))


def _zip_options() -> List[str]:
    return sorted(CALIFORNIA_ZIP_TO_CITY.keys(), key=int)


def _best_office_for_city(city: str) -> str:
    if city in FIELD_OFFICES:
        return FIELD_OFFICES[city]
    return f"Office local — {city} (N/A)" if city else "Office non défini"


def _seed(*parts: str) -> int:
    raw = "|".join(parts).encode()
    return int(hashlib.md5(raw).hexdigest()[:8], 16)


def _random_license_number(first_name: str, last_name: str, zip_code: str) -> str:
    r = random.Random(_seed(first_name, last_name, zip_code))
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return (
        f"{r.choice(letters)}"
        f"{r.randint(1000000, 9999999)}"
    )


def _generate_payload(
    first_name: str,
    last_name: str,
    dob: datetime.date,
    zip_code: str,
    city: str,
) -> str:
    # Payload AAMVA simplifié pour affichage/démo
    issue = datetime.date.today()
    exp = issue.replace(year=issue.year + 5)
    dl = _random_license_number(first_name, last_name, zip_code)

    return "\n".join(
        [
            "@",
            "ANSI 636026080102DL00410288ZA03290015DL",
            f"DAQ{dl}",
            f"DCS{last_name.upper()}",
            f"DAC{first_name.upper()}",
            f"DBB{dob.strftime('%m%d%Y')}",
            f"DBD{issue.strftime('%m%d%Y')}",
            f"DBA{exp.strftime('%m%d%Y')}",
            "DBC1",
            "DAU069 in",
            "DAYBRO",
            "DAG123 MAIN ST",
            f"DAI{city.upper()}",
            "DAJCA",
            f"DAK{zip_code}0000",
            "DCF00000000000000000",
            "DCGUSA",
        ]
    )


def _init_state() -> None:
    zips = _zip_options()
    cities = _city_options()

    if not zips or not cities:
        raise RuntimeError("Aucune donnée ZIP/Ville chargée.")

    if "selected_zip" not in st.session_state:
        st.session_state.selected_zip = "94015" if "94015" in zips else zips[0]

    if "selected_city" not in st.session_state:
        st.session_state.selected_city = get_city_from_zip(st.session_state.selected_zip) or cities[0]

    if "generated_payload" not in st.session_state:
        st.session_state.generated_payload = ""


def _sync_city_from_zip() -> None:
    z = st.session_state.selected_zip
    city = get_city_from_zip(z)
    if city:
        st.session_state.selected_city = city


def _sync_zip_from_city() -> None:
    city = st.session_state.selected_city
    possible_zips = find_zips_by_city(city)
    if possible_zips:
        # ZIP le plus petit numériquement pour stabilité
        st.session_state.selected_zip = sorted(possible_zips, key=int)[0]


# -------------------------
# UI
# -------------------------
def main() -> None:
    _init_state()

    st.title("Simulateur Permis Californie")
    st.caption("Interface démo Streamlit avec liaison ZIP ↔ Ville.")

    with st.container():
        col_zip, col_city = st.columns(2)

        with col_zip:
            st.selectbox(
                "Code postal",
                options=_zip_options(),
                key="selected_zip",
                on_change=_sync_city_from_zip,
            )

        with col_city:
            st.selectbox(
                "Ville",
                options=_city_options(),
                key="selected_city",
                on_change=_sync_zip_from_city,
            )

        city = st.session_state.selected_city
        office = _best_office_for_city(city)

        st.selectbox(
            "Field Office",
            options=[office],
            index=0,
            disabled=True,
            key="field_office_display",
        )

    st.markdown("---")
    st.subheader("Informations titulaire")

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        first_name = st.text_input("Prénom", value="John")
    with col_b:
        last_name = st.text_input("Nom", value="Doe")
    with col_c:
        dob = st.date_input(
            "Date de naissance",
            value=datetime.date(1990, 1, 1),
            min_value=datetime.date(1900, 1, 1),
            max_value=datetime.date.today(),
        )

    if st.button("Générer la carte", type="primary"):
        payload = _generate_payload(
            first_name=first_name,
            last_name=last_name,
            dob=dob,
            zip_code=st.session_state.selected_zip,
            city=st.session_state.selected_city,
        )
        st.session_state.generated_payload = payload

    if st.session_state.generated_payload:
        st.success("Carte générée avec succès.")
        st.write("**Résumé**")
        st.write(f"- Prénom: {first_name}")
        st.write(f"- Nom: {last_name}")
        st.write(f"- Code postal: {st.session_state.selected_zip}")
        st.write(f"- Ville: {st.session_state.selected_city}")
        st.write(f"- Field Office: {office}")

        with st.expander("Afficher payload AAMVA (démo)"):
            st.code(st.session_state.generated_payload, language="text")


if __name__ == "__main__":
    main()
