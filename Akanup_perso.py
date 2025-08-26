# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from datetime import date, datetime
from streamlit_calendar import calendar

# --- CONFIGURATION DE L'APPLICATION ---
PARTICIPANTS = ["Akanup", "Client", "Formateur"] 
DATE_DEBUT = date.today() 
COULEUR_ACCENT_AKANUP = "#FF6C73"  # Pour les sélections dans le calendrier (Corail/Rouge)
COULEUR_HIGHLIGHT_AKANUP = "#121440" # Pour le surlignage dans le tableau (Bleu nuit)
# --- FIN DE LA CONFIGURATION ---


# --- FONCTIONS UTILES (Ne pas modifier) ---
def highlight_common_days(row):
    """Surligne les jours communs avec la couleur de la marque."""
    if row['Total'] == len(PARTICIPANTS):
        return [f'background-color: {COULEUR_HIGHLIGHT_AKANUP}20'] * len(row)
    return [''] * len(row)

# --- CŒUR DE L'APPLICATION STREAMLIT ---
st.set_page_config(page_title="Planificateur Akanup", layout="wide")

try:
    st.image("logo_akanup.png", width=200)
except:
    st.write("Logo Akanup (logo non trouvé)")

# <--- MODIFIÉ : Le titre de l'application a été mis à jour.
st.title("📅 Formation / Accompagnement Akanup")
st.write("Choisissez qui vous êtes, puis **cliquez sur les dates** du calendrier pour indiquer vos disponibilités. Recliquez sur une date pour la désélectionner.")

# Initialisation de l'état de la session
if 'selections' not in st.session_state:
    st.session_state.selections = {nom: set() for nom in PARTICIPANTS}
if 'calendar_view_date' not in st.session_state:
    st.session_state.calendar_view_date = DATE_DEBUT

# Création des deux colonnes
col1, col2 = st.columns([1, 2])

with col1:
    st.header("1. Qui êtes-vous ?")
    personne_active = st.selectbox("Sélectionnez un participant :", options=PARTICIPANTS)

    st.header("2. Tableau des résultats")
    jours_selectionnes_tous = [jour for sous_liste in st.session_state.selections.values() for jour in sous_liste]
    if jours_selectionnes_tous:
        df = pd.DataFrame(index=sorted(list(set(jours_selectionnes_tous))))
        for nom, dispo_set in st.session_state.selections.items():
            df[nom] = ["✅" if jour in dispo_set else "" for jour in df.index]
        
        df['Total'] = df.apply(lambda row: sum(1 for x in row if x == "✅"), axis=1)
        df_sorted = df.sort_values(by='Total', ascending=False)
        
        jours_communs = df_sorted[df_sorted['Total'] == len(PARTICIPANTS)]
        if not jours_communs.empty:
            st.success(f"🎉 **{len(jours_communs)} jour(s) commun(s) trouvé(s) !**")
        
        st.dataframe(df_sorted.style.apply(highlight_common_days, axis=1), use_container_width=True)
    else:
        st.info("Aucune date n'a encore été sélectionnée.")

with col2:
    st.header(f"3. Calendrier pour : **{personne_active}**")
    
    calendar_options = {
        "headerToolbar": {
            "left": "prev,next today",
            "center": "title",
            "right": "dayGridMonth,dayGridWeek",
        },
        "initialDate": str(st.session_state.calendar_view_date),
        "timeZone": "UTC",
    }

    events_a_afficher = []
    for jour_str in st.session_state.selections.get(personne_active, set()):
        events_a_afficher.append({
            "title": "Disponible",
            "start": jour_str,
            "end": jour_str,
            "color": COULEUR_ACCENT_AKANUP,
        })

    resultat_calendrier = calendar(
        events=events_a_afficher,
        options=calendar_options,
    )

    if resultat_calendrier and resultat_calendrier.get("callback") == "dateClick":
        date_cliquee_iso = resultat_calendrier.get("dateClick", {}).get("date")
        
        if date_cliquee_iso:
            date_cliquee_str = date_cliquee_iso[:10]

            st.session_state.calendar_view_date = date_cliquee_str

            selections_personne = st.session_state.selections[personne_active]
            
            if date_cliquee_str in selections_personne:
                selections_personne.remove(date_cliquee_str)
            else:
                selections_personne.add(date_cliquee_str)
            
            st.session_state.selections[personne_active] = selections_personne
            st.rerun()