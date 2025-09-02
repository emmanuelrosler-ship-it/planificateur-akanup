# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection
from streamlit_calendar import calendar

# --- CONFIGURATION DE L'APPLICATION ---
PARTICIPANTS = ["Akanup", "Client", "Formateur"]
DATE_DEBUT = date.today()

COULEURS_PARTICIPANTS = {
    "Akanup": "#FF6C73",    # Corail/Rouge
    "Client": "#121440",    # Bleu nuit
    "Formateur": "#28a745"  # Vert
}
COULEUR_HIGHLIGHT_AKANUP = "#121440"

NOM_FEUILLE_DE_CALCUL = "Feuille 1" # VÉRIFIEZ QUE CE NOM CORRESPOND À VOTRE GOOGLE SHEET
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
    st.error(f"Erreur de connexion à la base de données. Vérifiez les 'Secrets'. Erreur: {e}")
    st.stop()

# --- Fonctions pour lire et écrire dans la base de données ---
@st.cache_data(ttl=5) # <--- On garde un cache très court pour la performance et éviter les erreurs de quota
def read_data_from_gsheet():
    """Lit les données depuis la feuille de calcul."""
    try:
        df = conn.read(worksheet=NOM_FEUILLE_DE_CALCUL, usecols=[0, 1])
        df = df.dropna(how="all")
        df['Participant'] = df['Participant'].astype(str)
        df['Date'] = df['Date'].astype(str)
        return df
    except Exception as e:
        st.error(f"Impossible de lire la feuille '{NOM_FEUILLE_DE_CALCUL}'. Vérifiez que le nom de l'onglet est correct. Erreur: {e}")
        return pd.DataFrame(columns=["Participant", "Date"])

def update_database(df_to_write):
    """Réécrit la feuille de calcul avec les nouvelles données."""
    try:
        df_to_write = df_to_write[['Participant', 'Date']]
        conn.update(worksheet=NOM_FEUILLE_DE_CALCUL, data=df_to_write)
        # On vide le cache immédiatement après une écriture pour garantir la fraîcheur
        read_data_from_gsheet.clear()
    except Exception as e:
        st.error(f"Impossible de mettre à jour la feuille de calcul. Erreur: {e}")

# --- INTERFACE UTILISATEUR ---
try:
    st.image("logo_akanup.png", width=200)
except:
    st.write("Logo Akanup (logo non trouvé)")

st.title("📅 Formation / Accompagnement Akanup")
st.write("Choisissez qui vous êtes, puis **cliquez sur les dates** pour indiquer vos disponibilités.")

if 'calendar_view_date' not in st.session_state:
    st.session_state.calendar_view_date = DATE_DEBUT

# On lit les données à chaque exécution, en profitant du cache intelligent
all_selections_df = read_data_from_gsheet()

col1, col2 = st.columns([1, 2])

with col1:
    st.header("1. Qui êtes-vous ?")
    personne_active = st.selectbox("Sélectionnez un participant :", options=PARTICIPANTS, key="participant_select")
    
    st.header("2. Tableau des résultats")
    if not all_selections_df.empty:
        pivot_df = all_selections_df.pivot_table(index='Date', columns='Participant', aggfunc='size', fill_value=0)
        for participant in PARTICIPANTS:
            if participant not in pivot_df.columns: pivot_df[participant] = 0
        pivot_df = pivot_df[PARTICIPANTS]
        for participant in PARTICIPANTS:
            pivot_df[participant] = pivot_df[participant].apply(lambda x: "✅" if x > 0 else "")
        pivot_df['Total'] = pivot_df.apply(lambda row: sum(1 for x in row if x == "✅"), axis=1)
        df_sorted = pivot_df.sort_values(by=['Total', 'Date'], ascending=[False, True])
        jours_communs = df_sorted[df_sorted['Total'] == len(PARTICIPANTS)]
        if not jours_communs.empty:
            st.success(f"🎉 **{len(jours_communs)} jour(s) commun(s) trouvé(s) !**")
        st.dataframe(df_sorted.style.apply(highlight_common_days, axis=1), use_container_width=True)
    else:
        st.info("Aucune date n'a encore été sélectionnée.")

# --- LOGIQUE DE GESTION DU CALENDRIER ET DES CLICS ---
with col2:
    st.header(f"3. Calendrier (vue pour : **{personne_active}**)")
    calendar_options = { "headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth,dayGridWeek"}, "initialDate": str(st.session_state.calendar_view_date), "timeZone": "UTC" }
    
    events_a_afficher = []
    if not all_selections_df.empty:
        for index, row in all_selections_df.iterrows():
            events_a_afficher.append({
                "title": f"Disponible {row['Participant']}",
                "start": row['Date'],
                "end": row['Date'],
                "color": COULEURS_PARTICIPANTS.get(row['Participant'], "#D3D3D3"),
            })
    
    resultat_calendrier = calendar(events=events_a_afficher, options=calendar_options, key="stable_calendar")

if resultat_calendrier and resultat_calendrier.get("callback") == "dateClick":
    date_cliquee_iso = resultat_calendrier.get("dateClick", {}).get("date")
    if date_cliquee_iso:
        date_cliquee_str = date_cliquee_iso[:10]
        st.session_state.calendar_view_date = date_cliquee_str

        selection_existante = all_selections_df[(all_selections_df['Participant'] == personne_active) & (all_selections_df['Date'] == date_cliquee_str)]
        
        if not selection_existante.empty:
            all_selections_df = all_selections_df.drop(selection_existante.index)
        else:
            nouvelle_ligne = pd.DataFrame([{"Participant": personne_active, "Date": date_cliquee_str}])
            all_selections_df = pd.concat([all_selections_df, nouvelle_ligne], ignore_index=True)
        
        update_database(all_selections_df)
        st.rerun()

# --- BOUTONS D'ACTION EN BAS DE PAGE ---
st.markdown("---")
action_col1, action_col2 = st.columns([3, 1])

with action_col1:
    if st.button("🔄 Rafraîchir les données"):
        read_data_from_gsheet.clear() # On force la relecture des données fraîches
        st.rerun()

with action_col2:
    if st.button("🗑️ Vider le calendrier", type="secondary"):
        empty_df = pd.DataFrame(columns=["Participant", "Date"])
        update_database(empty_df)
        st.rerun()
