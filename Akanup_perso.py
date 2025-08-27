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
            if participant in pivot_df.columns:
                pivot_df[participant] = pivot_df[participant].apply(lambda x: "✅" if x > 0 else "")
            else:
                pivot_df[participant] = "" # Ajoute une colonne vide si le participant n'a rien sélectionné

        # Calcul du total et tri
        pivot_df['Total'] = pivot_df.apply(lambda row: sum(1 for x in row if x == "✅"), axis=1)
        df_sorted = pivot_df.sort_values(by='Total', ascending=False)
        
        jours_communs = df_sorted[df_sorted['Total'] == len(PARTICIPANTS)]
        if not jours_communs.empty:
            st.success(f"🎉 **{len(jours_communs)} jour(s) commun(s) trouvé(s) !**")
        
        st.dataframe(df_sorted.style.apply(highlight_common_days, axis=1), use_container_width=True)
    else:
        st.info("Aucune date n'a encore été sélectionnée.")

with col2:
    st.header(f"3. Calendrier pour : **{personne_active}**")
    
    calendar_options = {
        "headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth,dayGridWeek"},
        "initialDate": str(st.session_state.calendar_view_date),
        "timeZone": "UTC",
    }
    
    # Création des "événements" à afficher : les dates sélectionnées par la personne active
    events_a_afficher = []
    if not all_selections_df.empty:
        selections_personne = set(all_selections_df[all_selections_df['Participant'] == personne_active]['Date'])
        for jour_str in selections_personne:
            events_a_afficher.append({
                "title": "Disponible",
                "start": jour_str,
                "end": jour_str,
                "color": COULEUR_ACCENT_AKANUP,
            })

    resultat_calendrier = calendar(events=events_a_afficher, options=calendar_options)

    # --- LOGIQUE DE MISE À JOUR DE LA BASE DE DONNÉES ---
    if resultat_calendrier and resultat_calendrier.get("callback") == "dateClick":
        date_cliquee_iso = resultat_calendrier.get("dateClick", {}).get("date")
        
        if date_cliquee_iso:
            date_cliquee_str = date_cliquee_iso[:10]
            st.session_state.calendar_view_date = date_cliquee_str

            # On vérifie si la sélection existe déjà dans le DataFrame
            selection_existante = all_selections_df[
                (all_selections_df['Participant'] == personne_active) & 
                (all_selections_df['Date'] == date_cliquee_str)
            ]

            if not selection_existante.empty:
                # Si elle existe, on la supprime du DataFrame
                all_selections_df = all_selections_df.drop(selection_existante.index)
            else:
                # Sinon, on l'ajoute comme une nouvelle ligne
                nouvelle_ligne = pd.DataFrame([{"Participant": personne_active, "Date": date_cliquee_str}])
                all_selections_df = pd.concat([all_selections_df, nouvelle_ligne], ignore_index=True)
            
            # On envoie le DataFrame mis à jour vers Google Sheets
            update_database(all_selections_df)
            st.rerun()
