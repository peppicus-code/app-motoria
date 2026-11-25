import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime, date
import time
import random
import secrets
import string

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="Portale Educazione Motoria",
    page_icon="🏃‍♂️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- STILE GRAFICO SPORTIVO & OTTIMIZZAZIONE SMARTPHONE ---
st.markdown("""
<style>
    /* Pulsanti grandi e comodi da smartphone */
    div.stButton > button {
        min-height: 54px;
        font-size: 17px !important;
        font-weight: 700 !important;
        border-radius: 12px !important;
        border: 2px solid #1E88E5;
        transition: all 0.2s ease-in-out;
    }
    div.stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(30, 136, 229, 0.3);
    }
    /* Pulsanti primari (es. azioni principali / elimina) */
    div.stButton > button[kind="primary"] {
        background-color: #E53935 !important;
        border-color: #B71C1C !important;
        color: white !important;
    }
    /* Titoli con accento sportivo */
    h1, h2, h3 {
        color: #0D47A1;
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }
    /* Card per segnapunti e squadre */
    .sport-card {
        background: linear-gradient(135deg, #0D47A1 0%, #1976D2 100%);
        color: white;
        padding: 20px;
        border-radius: 16px;
        text-align: center;
        box-shadow: 0 6px 16px rgba(0,0,0,0.15);
        margin-bottom: 12px;
    }
    .sport-card-b {
        background: linear-gradient(135deg, #1B5E20 0%, #388E3C 100%);
        color: white;
        padding: 20px;
        border-radius: 16px;
        text-align: center;
        box-shadow: 0 6px 16px rgba(0,0,0,0.15);
        margin-bottom: 12px;
    }
    .squadra-box {
        background-color: #F1F8E9;
        border-left: 6px solid #2E7D32;
        padding: 14px;
        border-radius: 10px;
        margin-bottom: 10px;
        color: #1B5E20;
    }
    /* Input più leggibili su mobile */
    input, select, textarea {
        font-size: 16px !important;
    }
</style>
""", unsafe_allow_html=True)

# --- CONNESSIONE A SUPABASE ---
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# --- FUNZIONI DI UTILITÀ & SICUREZZA ---
def genera_codice_sicuro(lunghezza=8):
    """Genera un codice casuale crittograficamente sicuro per tutelare la privacy dei minori."""
    # Esclude caratteri ambigui (0, O, 1, I, L) per evitare errori di lettura su smartphone
    alfabeto = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alfabeto) for _ in range(lunghezza))

def maschera_codice(codice):
    """Mostra solo i primi 2 e gli ultimi 2 caratteri del codice nella tabella generale."""
    if not codice or len(codice) < 4:
        return "****"
    return f"{codice[:2]}****{codice[-2:]}"

def calcola_voto(tipo_test, valore):
    """Calcolo automatico voti (personalizzabile)"""
    if tipo_test == "Corsa 1000m (secondi)":
        if valore <= 210: return 10.0
        elif valore <= 230: return 9.0
        elif valore <= 250: return 8.0
        elif valore <= 270: return 7.0
        elif valore <= 300: return 6.0
        else: return 5.0
    elif tipo_test == "Salto in lungo da fermo (cm)":
        if valore >= 220: return 10.0
        elif valore >= 200: return 9.0
        elif valore >= 180: return 8.0
        elif valore >= 160: return 7.0
        elif valore >= 140: return 6.0
        else: return 5.0
    elif tipo_test == "Addominali in 1 minuto (ripetizioni)":
        if valore >= 45: return 10.0
        elif valore >= 38: return 9.0
        elif valore >= 30: return 8.0
        elif valore >= 22: return 7.0
        elif valore >= 15: return 6.0
        else: return 5.0
    return 6.0

def genera_torneo_italiana(squadre, partite_per_squadra, totale_partite):
    """
    Genera gli abbinamenti per un torneo all'italiana parziale o completo,
    bilanciando gli incontri ed evitando che una squadra giochi due volte di fila.
    """
    n = len(squadre)
    if n < 2:
        return None, "Inserisci almeno 2 classi/squadre partecipanti."
    if n * partite_per_squadra != 2 * totale_partite:
        return None, (
            f"Impossibile bilanciare il calendario: {n} squadre × {partite_per_squadra} partite a testa "
            f"richiedono {(n * partite_per_squadra) / 2:g} partite totali (hai inserito {totale_partite})."
        )
    if partite_per_squadra > n - 1:
        # Se ci sono più partite del girone singolo, consente andata/ritorno
        moltiplicatore = (partite_per_squadra // (n - 1)) + 1
    else:
        moltiplicatore = 1

    # Tentativi multipli per trovare un ordine senza partite consecutive per la stessa squadra
    for _ in range(300):
        conteggio = {s: 0 for s in squadre}
        sfide_usate = {}
        calendario = []
        possibile = True

        for turno in range(totale_partite):
            ultima_partita = calendario[-1] if calendario else (None, None)
            # Ordina le squadre dando priorità a chi ha giocato meno partite
            ordinate = squadre.copy()
            random.shuffle(ordinate)
            ordinate.sort(key=lambda x: conteggio[x])

            abbinamento_trovato = None
            for i in range(n):
                s1 = ordinate[i]
                if conteggio[s1] >= partite_per_squadra:
                    continue
                for j in range(i + 1, n):
                    s2 = ordinate[j]
                    if conteggio[s2] >= partite_per_squadra:
                        continue
                    chiave = tuple(sorted((s1, s2)))
                    if sfide_usate.get(chiave, 0) >= moltiplicatore:
                        continue
                    # Evita che una squadra giochi due partite consecutive se ci sono alternative
                    if s1 not in ultima_partita and s2 not in ultima_partita:
                        abbinamento_trovato = (s1, s2)
                        break
                if abbinamento_trovato:
                    break

            # Fallback se negli ultimi turni è inevitabile giocare di seguito
            if not abbinamento_trovato:
                for i in range(n):
                    s1 = ordinate[i]
                    if conteggio[s1] >= partite_per_squadra:
                        continue
                    for j in range(i + 1, n):
                        s2 = ordinate[j]
                        if conteggio[s2] >= partite_per_squadra:
                            continue
                        chiave = tuple(sorted((s1, s2)))
                        if sfide_usate.get(chiave, 0) < moltiplicatore:
                            abbinamento_trovato = (s1, s2)
                            break
                    if abbinamento_trovato:
                        break

            if not abbinamento_trovato:
                possibile = False
                break

            s1, s2 = abbinamento_trovato
            calendario.append((s1, s2))
            conteggio[s1] += 1
            conteggio[s2] += 1
            chiave = tuple(sorted((s1, s2)))
            sfide_usate[chiave] = sfide_usate.get(chiave, 0) + 1

        if possibile and len(calendario) == totale_partite:
            return calendario, None

    return None, "Non è stato possibile generare una combinazione valida con questi vincoli. Prova a modificare i numeri."

# --- GESTIONE SESSIONE ---
if "ruolo" not in st.session_state:
    st.session_state.ruolo = None
if "studente_corrente" not in st.session_state:
    st.session_state.studente_corrente = None
if "punti_a" not in st.session_state:
    st.session_state.punti_a = 0
if "punti_b" not in st.session_state:
    st.session_state.punti_b = 0
if "squadre_generate" not in st.session_state:
    st.session_state.squadre_generate = []
if "calendario_generato" not in st.session_state:
    st.session_state.calendario_generato = []
if "codice_proposto" not in st.session_state:
    st.session_state.codice_proposto = genera_codice_sicuro()

# --- SCHERMATA DI ACCESSO ---
if st.session_state.ruolo is None:
    st.title("🏃‍♂️ Portale Educazione Motoria")
    st.markdown("Seleziona la modalità di accesso:")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🎓 Area Studenti")
        codice_input = st.text_input("Inserisci il tuo Codice Personale:", type="password")
        if st.button("Entra come Studente", use_container_width=True):
            res = supabase.table("studenti").select("*, classi(nome)").eq("codice_personale", codice_input.strip().upper()).execute()
            if res.data:
                st.session_state.ruolo = "studente"
                st.session_state.studente_corrente = res.data[0]
                st.rerun()
            else:
                st.error("Codice personale non valido.")
    with col2:
        st.subheader("📋 Area Docente")
        try:
            res_pwd = supabase.table("impostazioni").select("valore").eq("chiave", "password_docente").execute()
            password_attuale = res_pwd.data[0]["valore"] if res_pwd.data else st.secrets["PASSWORD_DOCENTE"]
        except Exception:
            password_attuale = st.secrets["PASSWORD_DOCENTE"]
        pwd_input = st.text_input("Password Docente:", type="password")
        if st.button("Entra come Docente", use_container_width=True):
            if pwd_input == password_attuale:
                st.session_state.ruolo = "docente"
                st.rerun()
            else:
                st.error("Password errata.")
        with st.expander("🔑 Hai dimenticato o vuoi cambiare la password?"):
            st.caption("Usa il Codice Segreto (PUK) assegnato al docente per impostare una nuova password:")
