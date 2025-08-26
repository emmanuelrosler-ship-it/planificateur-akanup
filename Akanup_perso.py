# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection
from streamlit_calendar import calendar

# --- CONFIGURATION DE L'APPLICATION ---
PARTICIPANTS = ["Akanup", "Client", "Formateur"]
DATE_DEBUT = date.today()
COULEUR_ACCENT_AKANUP = "#FF6C73"  # Pour les sélections dans le calendrier (Corail/Rouge)
COULEUR_HIGHLIGHT_AKANUP = "#121440" # Pour le surlignage dans le tableau (Bleu nuit)
# --- FIN DE LA CONFIGURATION ---


# --- FONCTIONS UTILES ---
def highlight_common_days(row):
    """Surligne les jours communs avec la couleur de la marque."""
    if row['Total'] == len(PARTICIPANTS):
        return [f'background-color: {COULEUR_HIGHLIGHT_AKANUP}20'] * len(row)
    return [''] * len(row)

# --- CŒUR DE L'APPLICATION STREAMLIT ---
st.set_page_config(page_title="Planificateur Akanup", layout="wide")

# Connexion à la base de données Google Sheets (requiert les "Secrets" configurés)
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("Erreur de connexion à la base de données Google Sheets. Veuillez vérifier la configuration des 'Secrets' dans Streamlit Cloud.")
    st.stop()

# --- Fonctions pour lire et écrire dans la base de données ---
@st.cache_data(ttl=5) # Met en cache les données pendant 5 secondes pour éviter de surcharger l'API
def read_data():
    df = conn.read(worksheet="Feuille 1", usecols=[0, 1])
    df = df.dropna(how="all")
    return df

def update_database(df):
    conn.update(worksheet="Feuille 1", data=df)

# --- INTERFACE UTILISATEUR ---
try:
    st.image("logo_akanup.png", width=200)
except:
    st.write("Logo Akanup (logo non trouvé)")

st.title("📅 Formation / Accompagnement Akanup")
st.write("Choisissez qui vous êtes, puis **cliquez sur les dates** du calendrier pour indiquer vos disponibilités. Recliquez sur une date pour la désélectionner.")

# Initialisation de la mémoire de la session pour la vue du calendrier
if 'calendar_view_date' not in st.session_state:
    st.session_state.calendar_view_date = DATE_DEBUT

# Lecture des données depuis Google Sheets
all_selections_df = read_data()

# Création des deux colonnes
col1, col2 = st.columns([1, 2])

with col1:
    st.header("1. Qui êtes-vous ?")
    personne_active = st.selectbox("Sélectionnez un participant :", options=PARTICIPANTS)

    st.header("2. Tableau des résultats")
    if not all_selections_df.empty:
        # On s'assure que la colonne Date est bien du texte pour le pivot
        all_selections_df['Date'] = all_selections_df['Date'].astype(str)
        
        # On crée un tableau croisé pour avoir les participants en colonnes
        pivot_df = all_selections_df.pivot_table(index='Date', columns='Participant', aggfunc='size', fill_value=0)
        # On transforme les nombres en coches "✅"
        for participant in PARTICIPANTS:
            if par