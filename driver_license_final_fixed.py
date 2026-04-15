# Copie-colle ce bloc dans ton fichier (au-dessus de l'UI principale)
import calendar
import datetime
import streamlit as st
from typing import Optional

WEEKDAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]

def _month_year_key(prefix: str, dt: datetime.date):
    return f"{prefix}_{dt.year}_{dt.month}"

def custom_date_picker(label: str, default: Optional[datetime.date] = None) -> Optional[datetime.date]:
    """
    Affiche un calendrier interactif et retourne la date sélectionnée (datetime.date) ou None.
    Usage:
        selected = custom_date_picker("Date d'émission", default=datetime.date.today())
    """
    if default is None:
        default = datetime.date.today()

    # Initialisation session_state pour le mois affiché et la sélection
    if "cdp_display_month" not in st.session_state:
        st.session_state["cdp_display_month"] = datetime.date(default.year, default.month, 1)
    if "cdp_selected_date" not in st.session_state:
        st.session_state["cdp_selected_date"] = default

    # Container visuel
    st.markdown(f"**{label}**")
    cal_col1, cal_col2 = st.columns([3, 1])

    # Navigation mois / année
    with cal_col1:
        display = st.session_state["cdp_display_month"]
        prev_month = (display.replace(day=1) - datetime.timedelta(days=1)).replace(day=1)
        next_month = (display.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)

        nav_col1, nav_col2, nav_col3 = st.columns([1, 6, 1])
        with nav_col1:
            if st.button("◀", key=_month_year_key("prev", display)):
                st.session_state["cdp_display_month"] = prev_month
        with nav_col2:
            # Titre mois + année
            st.markdown(f"### {display.strftime('%B %Y')}")
        with nav_col3:
            if st.button("▶", key=_month_year_key("next", display)):
                st.session_state["cdp_display_month"] = next_month

    # Ligne mois rapide (sélection directe)
    months = [datetime.date(display.year, m, 1) for m in range(1, 13)]
    month_labels = [m.strftime("%b") for m in months]
    sel_month_idx = months.index(display) if display.month in range(1,13) else 0
    chosen_month = st.selectbox("Mois", options=month_labels, index=sel_month_idx, key=_month_year_key("select_month", display))
    # si l'utilisateur change via selectbox, mettre à jour le mois affiché
    chosen_month_num = month_labels.index(chosen_month) + 1
    if chosen_month_num != display.month:
        st.session_state["cdp_display_month"] = display.replace(month=chosen_month_num, day=1)

    # Construire la grille du mois
    year = st.session_state["cdp_display_month"].year
    month = st.session_state["cdp_display_month"].month
    cal = calendar.Calendar(firstweekday=0)  # Monday start
    month_days = list(cal.itermonthdates(year, month))

    # Affichage des en-têtes de jours
    cols = st.columns(7)
    for i, wd in enumerate(WEEKDAYS):
        cols[i].markdown(f"**{wd}**")

    # Affichage des jours en grille (6 lignes x 7 colonnes)
    day_cols = None
    for week_idx in range(6):
        week = month_days[week_idx*7:(week_idx+1)*7]
        cols = st.columns(7)
        for i, day in enumerate(week):
            is_current_month = (day.month == month)
            key = f"cdp_day_{year}_{month}_{week_idx}_{i}_{day.isoformat()}"
            label_day = str(day.day)
            # Style : jours hors mois en gris, jours du mois en bouton normal
            if is_current_month:
                # Mettre en évidence le jour sélectionné
                if st.session_state.get("cdp_selected_date") == day:
                    btn_label = f"**[{label_day}]**"
                else:
                    btn_label = label_day
                if cols[i].button(btn_label, key=key):
                    st.session_state["cdp_selected_date"] = day
            else:
                # Afficher en texte non cliquable (ou bouton désactivé)
                cols[i].markdown(f"<span style='color:#9aa0a6'>{label_day}</span>", unsafe_allow_html=True)

    # Bouton pour effacer la sélection
    clear_col, spacer_col = st.columns([1, 6])
    with clear_col:
        if st.button("Effacer la date", key="cdp_clear"):
            st.session_state["cdp_selected_date"] = None

    # Retourner la date sélectionnée (convertie en datetime.date ou None)
    selected = st.session_state.get("cdp_selected_date")
    return selected

# Exemple d'utilisation (remplace ton st.date_input par ceci)
# selected_date = custom_date_picker("Date d'émission", default=datetime.date.today())
# st.write("Date sélectionnée :", selected_date)
