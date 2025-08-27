# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection
from streamlit_calendar import calendar

# --- CONFIGURATION DE L'APPLICATION ---
PARTICIPANTS = ["Akanup", "Client", "Formateur"]
DATE_DEBUT = date.today()
COULEUR_ACCENT_AKANUP = "#FF6C73"
COULEUR_HIGHLIGHT_AKANUP = "#121440"
# --- FIN DE LA CONFIGURATION ---


# --- FONCTIONS UTILES ---
def highlight_common_days(row):
    """Surligne les jours communs avec la couleur de la marque."""
    if row['Total'] == len(PARTICIPANTS):
        return [f'background-color: {COULEUR_HIGHLIGHT_AKANUP}20'] * len(row)
    return [''] * len(row)

# --- CŒUR DE L'APPLICATION STREAMLIT ---
st.set_page_config(page_title="Planificateur Akanup", layout="wide")

# Connexion à la base de données Google Sheets
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("Erreur de connexion à la base de données. Vérifiez les 'Secrets'.")
    st.stop()

# --- Fonctions pour lire et écrire dans la base de données ---
@st.cache_data(ttl=5) # Cache court pour être réactif
def read_data():
    df = conn.read(worksheet="Feuille 1", usecols=[0, 1])
    df = df.dropna(how="all")
    df['Participant'] = df['Participant'].astype(str)
    df['Date'] = df['Date'].astype(str)
    return df

def update_database(df_to_write):
    """Réécrit la feuille de calcul avec le nouveau DataFrame."""
    conn.update(worksheet="Feuille 1", data=df_to_write)

# --- INTERFACE UTILISATEUR ---
try:
    st.image("logo_akanup.png", width=200)
except:
    st.write("Logo Akanup (logo non trouvé)")

st.title("📅 Formation / Accompagnement Akanup")
st.write("Choisissez qui vous êtes, puis **cliquez sur les dates** pour indiquer vos disponibilités.")

if 'calendar_view_date' not in st.session_state:
    st.session_state.calendar_view_date = DATE_DEBUT

all_selections_df = read_data()

col1, col2 = st.columns([1, 2])

with col1:
    st.header("1. Qui êtes-vous ?")
    personne_active = st.selectbox("Sélectionnez un participant :", options=PARTICIPANTS, key="participant_select")

    st.header("2. Tableau des résultats")
    if not all_selections_df.empty:
        pivot_df = all_selections_df.pivot_table(index='Date', columns='Participant', aggfunc='size', fill_value=0)
        for participant in PARTICIPANTS:
            if participant in pivot_df.columns:
                pivot_df[participant] = pivot_df[participant].apply(lambda x: "✅" if x > 0 else "")
            else:
                pivot_df[participant] = ""
        pivot_df['Total'] = pivot_df.apply(lambda row: sum(1 for x in row if x == "✅"), axis=1)
        df_sorted = pivot_df.sort_values(by=['Total', 'Date'], ascending=[False, True])
        jours_communs = df_sorted[df_sorted['Total'] == len(PARTICIPANTS)]
        if not jours_communs.empty:
            st.success(f"🎉 **{len(jours_communs)} jour(s) commun(s) trouvé(s) !**")
        st.dataframe(df_sorted.style.apply(highlight_common_days, axis=1), use_container_width=True)
    else:
        st.info("Aucune date n'a encore été sélectionnée.")

# --- LOGIQUE DE GESTION DU CALENDRIER ET DES CLICS ---

# On récupère les sélections de la personne active pour l'affichage
selections_personne = set()
if not all_selections_df.empty:
    selections_personne = set(all_selections_df[all_selections_df['Participant'] == personne_active]['Date'])

# Configuration et affichage du calendrier
with col2:
    st.header(f"3. Calendrier pour : **{personne_active}**")
    calendar_options = {
        "headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth,dayGridWeek"},
        "initialDate": str(st.session_state.calendar_view_date),
        "timeZone": "UTC",
    }
    events_a_afficher = [{"title": "Disponible", "start": jour, "end": jour, "color": COULEUR_ACCENT_AKANUP} for jour in selections_personne]
    
    # On stocke le résultat du calendrier dans une variable
    resultat_calendrier = calendar(events=events_a_afficher, options=calendar_options, key=f"cal_{personne_active}")

# On traite le résultat du clic APRES l'affichage, pour éviter la boucle
if resultat_calendrier and resultat_calendrier.get("callback") == "dateClick":
    date_cliquee_iso = resultat_calendrier.get("dateClick", {}).get("date")
    if date_cliquee_iso:
        date_cliquee_str = date_cliquee_iso[:10]
        st.session_state.calendar_view_date = date_cliquee_str

        # On modifie le DataFrame en mémoire
        selection_existante = all_selections_df[
            (all_selections_df['Participant'] == personne_active) & 
            (all_selections_df['Date'] == date_cliquee_str)
        ]

        if not selection_existante.empty:
            all_selections_df = all_selections_df.drop(selection_existante.index)
        else:
            nouvelle_ligne = pd.DataFrame([{"Participant": personne_active, "Date": date_cliquee_str}])
            all_selections_df = pd.concat([all_selections_df, nouvelle_ligne], ignore_index=True)
        
        # On met à jour la base de données et on vide le cache
        update_database(all_selections_df)
        read_data.clear()
        
        # On redémarre la page pour afficher le changement
        st.rerun()
