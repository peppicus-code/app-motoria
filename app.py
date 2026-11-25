import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime, date
import time
import random
import string
from itertools import combinations

# --- CONFIGURAZIONE PAGINA E STILE SPORTIVO ---
st.set_page_config(page_title="Portale Educazione Motoria", page_icon="🏅", layout="wide")

st.markdown("""
<style>
    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
        padding: 0.6rem 1rem;
        transition: all 0.2s ease;
    }
    .score-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        border: 2px solid #334155;
        color: white;
    }
    .match-card {
        background-color: #1e293b;
        border-left: 5px solid #10b981;
        padding: 12px 16px;
        border-radius: 8px;
        margin-bottom: 8px;
        color: #f8fafc;
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

# --- FUNZIONI DI UTILITÀ ---
def genera_codice_sicuro():
    """Genera un codice casuale anti-indovinamento per privacy GDPR minori"""
    numeri = ''.join(random.choices(string.digits, k=4))
    lettere = ''.join(random.choices(string.ascii_uppercase, k=2))
    return f"MTR-{numeri}-{lettere}"

def calcola_voto(tipo_test, valore):
    """Calcolo automatico voti (esempi personalizzabili)"""
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

def genera_calendario_italiana(squadre, partite_per_squadra, max_partite_totali=None):
    """Genera abbinamenti equilibrati per tornei all'italiana parziali o completi"""
    tutte_coppie = list(combinations(squadre, 2))
    random.shuffle(tutte_coppie)
    conteggio = {s: 0 for s in squadre}
    partite_scelte = []

    # Ordina le coppie dando priorità alle squadre con meno partite assegnate
    for _ in range(len(tutte_coppie) * 2):
        if max_partite_totali and len(partite_scelte) >= max_partite_totali:
            break
        candidati = [
            c for c in tutte_coppie
            if c not in partite_scelte
            and conteggio[c] < partite_per_squadra
            and conteggio[c] < partite_per_squadra
        ]
        if not candidati:
            break
        candidati.sort(key=lambda c: conteggio[c] + conteggio[c])
        scelta = candidati
        partite_scelte.append(scelta)
        conteggio[scelta] += 1
        conteggio[scelta] += 1

    return partite_scelte, conteggio

# --- GESTIONE SESSIONE ---
if "ruolo" not in st.session_state:
    st.session_state.ruolo = None
if "studente_corrente" not in st.session_state:
    st.session_state.studente_corrente = None
if "punti_a" not in st.session_state:
    st.session_state.punti_a = 0
if "punti_b" not in st.session_state:
    st.session_state.punti_b = 0
if "codice_generato" not in st.session_state:
    st.session_state.codice_generato = genera_codice_sicuro()

# --- SCHERMATA DI ACCESSO ---
if st.session_state.ruolo is None:
    st.title("🏅 Portale Educazione Motoria")
    st.caption("Piattaforma digitale per la gestione didattica, i test fisici e i tornei scolastici")

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.subheader("🎓 Area Studenti")
            st.write("Consulta i tuoi voti, la validità del certificato medico e le classifiche.")
            codice_input = st.text_input("Codice Personale Studente:", type="password", placeholder="Es. MTR-4821-XK")
            if st.button("Entra come Studente", type="primary", use_container_width=True):
                res = supabase.table("studenti").select("*, classi(nome)").eq("codice_personale", codice_input.strip()).execute()
                if res.data:
                    st.session_state.ruolo = "studente"
                    st.session_state.studente_corrente = res.data
                    st.rerun()
                else:
                    st.error("Codice personale non valido.")

    with col2:
        with st.container(border=True):
            st.subheader("📋 Area Docente")
            st.write("Accesso riservato all'insegnante (compatibile con Face ID / Impronta del telefono).")
            pwd_input = st.text_input("Password Docente:", type="password")
            if st.button("Entra come Docente", type="primary", use_container_width=True):
                if pwd_input == st.secrets["PASSWORD_DOCENTE"]:
                    st.session_state.ruolo = "docente"
                    st.rerun()
                else:
                    st.error("Password errata.")

    with st.expander("🔒 Informativa Sicurezza & Privacy Minori (GDPR)"):
        st.info(
            "• **Tutela Dati Minori:** I codici studente sono alfanumerici casuali non deducibili dal cognome.\n"
            "• **Accesso Biometrico:** Salvando la password docente nel portachiavi di iPhone/Android (Face ID o Impronta), l'accesso risulta protetto biometricamente."
        )

# --- AREA DOCENTE ---
elif st.session_state.ruolo == "docente":
    st.sidebar.title("🏅 Menu Docente")
    menu = st.sidebar.radio("Seleziona sezione:", [
        "1. Classi e Studenti",
        "2. Certificati Medici",
        "3. Test Fisici e Voti",
        "4. Cronometro / Timer",
        "5. Tornei & Generatore Partite",
        "6. Bacheca Avvisi",
        "7. Squadre & Segnapunti"
    ])
    st.sidebar.divider()
    if st.sidebar.button("🚪 Esci (Logout)", use_container_width=True):
        st.session_state.ruolo = None
        st.rerun()

    # 1. CLASSI E STUDENTI
    if menu == "1. Classi e Studenti":
        st.header("🏫 Gestione Classi e Studenti")
        tab1, tab2, tab3 = st.tabs(["➕ Aggiungi Classe", "➕ Aggiungi Studente", "🗑️ Elimina"])

        with tab1:
            nuova_classe = st.text_input("Nome nuova classe (es. 3A, 4B):")
            if st.button("Crea Classe", type="primary"):
                if nuova_classe:
                    try:
                        supabase.table("classi").insert({"nome": nuova_classe.strip()}).execute()
                        st.success(f"Classe {nuova_classe} creata!")
                        time.sleep(0.6)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Errore: {e}")

        with tab2:
            classi_data = supabase.table("classi").select("*").execute().data
            if not classi_data:
                st.warning("Crea prima almeno una classe!")
            else:
                mappa_classi = {c["nome"]: c["id"] for c in classi_data}
                classe_scelta = st.selectbox("Seleziona Classe:", list(mappa_classi.keys()))
                c_n1, c_n2 = st.columns(2)
                nome = c_n1.text_input("Nome Studente:")
                cognome = c_n2.text_input("Cognome Studente:")

                c_cod1, c_cod2 = st.columns([3, 1])
                codice = c_cod1.text_input("Codice Personale Studente (Privacy GDPR):", value=st.session_state.codice_generato)
                if c_cod2.button("🔄 Nuovo Codice", use_container_width=True):
                    st.session_state.codice_generato = genera_codice_sicuro()
                    st.rerun()

                scad_cert = st.date_input("Scadenza Certificato Medico:", value=date.today())
                note = st.text_area("Note riservate docente (es. esoneri parziali):")

                if st.button("Salva Studente", type="primary"):
                    if nome and cognome and codice:
                        try:
                            supabase.table("studenti").insert({
                                "classe_id": mappa_classi[classe_scelta],
                                "nome": nome.strip(),
                                "cognome": cognome.strip(),
                                "codice_personale": codice.strip(),
                                "scadenza_certificato": str(scad_cert),
                                "note": note
                            }).execute()
                            st.session_state.codice_generato = genera_codice_sicuro()
                            st.success(f"Studente {nome} {cognome} inserito!")
                            time.sleep(0.6)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Errore: {e}")

        with tab3:
            col_del1, col_del2 = st.columns(2)
            with col_del1:
                st.subheader("Elimina Studente")
                stud_del_list = supabase.table("studenti").select("id, nome, cognome, classi(nome)").execute().data
                if stud_del_list:
                    mappa_del_stud = {f"{s['cognome']} {s['nome']} ({s['classi']['nome'] if s['classi'] else ''})": s["id"] for s in stud_del_list}
                    stud_da_elim = st.selectbox("Scegli studente:", list(mappa_del_stud.keys()))
                    if st.button("🗑️ Elimina Studente", type="primary"):
