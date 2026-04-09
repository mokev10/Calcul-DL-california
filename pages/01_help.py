# pages/01_help.py
import streamlit as st

st.set_page_config(page_title="Aide - Calcul-DL-california", layout="centered")
st.title("Aide et documentation")

st.markdown("""
### But de l'application
Cette application simule la génération d'une carte de permis Californien et produit un code-barres PDF417.
Elle inclut un module vendorisé `pdf417gen` pour générer le code-barres.

### Vérifications rapides
- Si le PDF417 ne s'affiche pas, active le **Health Check** dans la sidebar de la page principale.
- Vérifie que le dossier `pdf417gen/` est à la racine du dépôt et contient `__init__.py`.

### Export et téléchargement
- **Télécharger PDF** : génère un PDF simple contenant les informations de la carte et la photo (si uploadée).
- **Télécharger SVG** : télécharge le SVG du code-barres PDF417.

### Rendre l'app privée
- Sur Streamlit Cloud → Settings → Access → choisir *Private* ou *Only people I invite*.

### Tests et CI
- Un workflow GitHub Actions exécute les tests unitaires (pytest) à chaque push.
- Les tests se trouvent dans le dossier `tests/`.

### Licence et vendorising
Consulte `VENDORING.md` pour la provenance et la licence du code vendorisé.

### Contact
Pour toute question ou bug, ouvre une issue sur le dépôt GitHub.
""")
