# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURATION DE L'APPLICATION ---
PARTICIPANTS = ["Akanup", "Client", "Formateur"] 
# ... le reste de votre config ...
# --- FIN DE LA CONFIGURATION ---

# --- CŒUR DE L'APPLICATION ---
st.set_page_config(page_title="Planificateur Akanup", layout="wide")

# Connexion à la base de données Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# --- Fonctions pour lire et écrire dans la base de données ---
def read_data():
    df = conn.read(worksheet="Feuille 1", usecols=[0, 1], ttl=5)
    df = df.dropna(how="all") # Enlève les lignes vides
    return df

def update_database(df):
    conn.update(worksheet="Feuille 1", data=df)

# On lit les données une seule fois au début
all_selections_df = read_data()

# ... Votre interface utilisateur (titre, logo, etc.) ...
st.title("📅 Formation / Accompagnement Akanup")
# ...

# Logique de l'application
col1, col2 = st.columns([1, 2])

with col1:
    personne_active = st.selectbox("Qui êtes-vous ?", options=PARTICIPANTS)
    
    # Affichage du tableau des résultats (basé sur le DataFrame lu depuis Google Sheets)
    if not all_selections_df.empty:
        # On pivote les données pour avoir les participants en colonnes
        pivot_df = all_selections_df.pivot_table(index='Date', columns='Participant', aggfunc='size', fill_value=0)
        # ... le reste de votre logique d'affichage du tableau ...
    
with col2:
    # ... Votre logique d'affichage du calendrier ...
    
    # Quand un clic est détecté
    if resultat_calendrier and resultat_calendrier.get("callback") == "dateClick":
        date_cliquee_str = ... # (votre logique pour extraire la date)

        # On vérifie si la sélection existe déjà
        selection_existante = all_selections_df[
            (all_selections_df['Participant'] == personne_active) & 
            (all_selections_df['Date'] == date_cliquee_str)
        ]

        if not selection_existante.empty:
            # Si elle existe, on la supprime
            all_selections_df = all_selections_df.drop(selection_existante.index)
        else:
            # Sinon, on l'ajoute
            nouvelle_ligne = pd.DataFrame([{"Participant": personne_active, "Date": date_cliquee_str}])
            all_selections_df = pd.concat([all_selections_df, nouvelle_ligne], ignore_index=True)
        
        # On met à jour la base de données en ligne
        update_database(all_selections_df)
        st.rerun()
