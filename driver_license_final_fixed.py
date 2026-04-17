import streamlit as st

st.set_page_config(page_title="Sélecteur Pays", layout="centered")

st.title("Sélecteur de pays")

# Options du menu déroulant
options = [
    "United States (US)",
    "Canada (CAN)"
]

selection = st.selectbox("Choisissez un pays :", options)

# Extraire l'abréviation entre parenthèses
def extract_code(label: str) -> str:
    if "(" in label and ")" in label:
        return label.split("(")[-1].split(")")[0].strip()
    return ""

code = extract_code(selection)

st.markdown(f"**Sélection :** {selection}")
st.markdown(f"**Code :** {code}")
