import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime, date
import time

# Configurazione pagina
st.set_page_config(page_title="Portale Educazione Motoria", page_icon="🏃‍♂️", layout="wide")

# Connessione a Supabase
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# --- FUNZIONI DI UTILITÀ ---
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

# --- GESTIONE SESSIONE ---
if "ruolo" not in st.session_state:
    st.session_state.ruolo = None
if "studente_corrente" not in st.session_state:
    st.session_state.studente_corrente = None

# --- SCHERMATA DI ACCESSO ---
if st.session_state.ruolo is None:
    st.title("🏃‍♂️ Portale Educazione Motoria")
    st.markdown("Seleziona la modalità di accesso:")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🎓 Area Studenti")
        codice_input = st.text_input("Inserisci il tuo Codice Personale:", type="password")
        if st.button("Entra come Studente", use_container_width=True):
            res = supabase.table("studenti").select("*, classi(nome)").eq("codice_personale", codice_input.strip()).execute()
            if res.data:
                st.session_state.ruolo = "studente"
                st.session_state.studente_corrente = res.data[0]
                st.rerun()
            else:
                st.error("Codice personale non valido.")

    with col2:
        st.subheader("📋 Area Docente")
        pwd_input = st.text_input("Password Docente:", type="password")
        if st.button("Entra come Docente", use_container_width=True):
            if pwd_input == st.secrets["PASSWORD_DOCENTE"]:
                st.session_state.ruolo = "docente"
                st.rerun()
            else:
                st.error("Password errata.")

# --- AREA DOCENTE ---
elif st.session_state.ruolo == "docente":
    st.sidebar.title("📋 Menu Docente")
    menu = st.sidebar.radio("Seleziona sezione:", [
        "1. Classi e Studenti",
        "2. Certificati Medici",
        "3. Test Fisici e Voti",
        "4. Cronometro / Timer",
        "5. Tornei e Classifiche",
        "6. Bacheca Avvisi"
    ])
    if st.sidebar.button("🚪 Esci (Logout)"):
        st.session_state.ruolo = None
        st.rerun()

    # 1. CLASSI E STUDENTI
    if menu == "1. Classi e Studenti":
        st.header("🏫 Gestione Classi e Studenti")
        tab1, tab2, tab3 = st.tabs(["➕ Aggiungi Classe", "➕ Aggiungi Studente", "🗑️ Elimina Classe / Studente"])

        with tab1:
            nuova_classe = st.text_input("Nome nuova classe (es. 3A, 4B):")
            if st.button("Crea Classe"):
                if nuova_classe:
                    try:
                        supabase.table("classi").insert({"nome": nuova_classe.strip()}).execute()
                        st.success(f"Classe {nuova_classe} creata!")
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
                nome = st.text_input("Nome Studente:")
                cognome = st.text_input("Cognome Studente:")
                codice = st.text_input("Codice Personale per accesso studente (es. ROSSI24):")
                scad_cert = st.date_input("Scadenza Certificato Medico:", value=date.today())
                note = st.text_area("Note eventuali (es. esoneri parziali, allergie):")

                if st.button("Salva Studente"):
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
                            st.success(f"Studente {nome} {cognome} inserito!")
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
                    stud_da_elim = st.selectbox("Scegli studente da eliminare:", list(mappa_del_stud.keys()))
                    if st.button("🗑️ Elimina Studente", type="primary"):
                        supabase.table("studenti").delete().eq("id", mappa_del_stud[stud_da_elim]).execute()
                        st.success("Studente eliminato!")
                        st.rerun()
                else:
                    st.info("Nessuno studente da eliminare.")

            with col_del2:
                st.subheader("Elimina Classe")
                classi_del_list = supabase.table("classi").select("*").execute().data
                if classi_del_list:
                    mappa_del_classi = {c["nome"]: c["id"] for c in classi_del_list}
                    classe_da_elim = st.selectbox("Scegli classe da eliminare:", list(mappa_del_classi.keys()))
                    st.caption("⚠️ Attenzione: eliminando la classe verranno eliminati anche tutti gli studenti al suo interno.")
                    if st.button("🗑️ Elimina Classe", type="primary"):
                        supabase.table("classi").delete().eq("id", mappa_del_classi[classe_da_elim]).execute()
                        st.success("Classe eliminata!")
                        st.rerun()
                else:
                    st.info("Nessuna classe da eliminare.")

        st.divider()
        st.subheader("Elenco Studenti Registrati")
        studenti_list = supabase.table("studenti").select("nome, cognome, codice_personale, scadenza_certificato, note, classi(nome)").execute().data
        if studenti_list:
            df = pd.DataFrame([{
                "Classe": s["classi"]["nome"] if s["classi"] else "",
                "Cognome": s["cognome"],
                "Nome": s["nome"],
                "Codice": s["codice_personale"],
                "Scadenza Certificato": s["scadenza_certificato"],
                "Note": s["note"]
            } for s in studenti_list])
            st.dataframe(df, use_container_width=True)

    # 2. CERTIFICATI MEDICI
    elif menu == "2. Certificati Medici":
        st.header("🩺 Controllo Scadenze Certificati Medici")
        studenti_list = supabase.table("studenti").select("id, nome, cognome, scadenza_certificato, classi(nome)").execute().data
        oggi = date.today()
        for s in studenti_list:
            scad = datetime.strptime(s["scadenza_certificato"], "%Y-%m-%d").date()
            giorni = (scad - oggi).days
            classe_nome = s["classi"]["nome"] if s["classi"] else ""
            if giorni < 0:
                st.error(f"❌ **{s['cognome']} {s['nome']}** ({classe_nome}) - SCADUTO il {scad.strftime('%d/%m/%Y')}")
            elif giorni <= 30:
                st.warning(f"⚠️ **{s['cognome']} {s['nome']}** ({classe_nome}) - In scadenza tra {giorni} giorni ({scad.strftime('%d/%m/%Y')})")
            else:
                st.success(f"✅ **{s['cognome']} {s['nome']}** ({classe_nome}) - Valido fino al {scad.strftime('%d/%m/%Y')}")

    # 3. TEST FISICI E VOTI
    elif menu == "3. Test Fisici e Voti":
        st.header("⏱️ Registrazione Test Fisici e Calcolo Voti")
        studenti_list = supabase.table("studenti").select("id, nome, cognome, classi(nome)").execute().data
        if not studenti_list:
            st.warning("Nessuno studente registrato.")
        else:
            mappa_stud = {f"{s['cognome']} {s['nome']} ({s['classi']['nome']})": s["id"] for s in studenti_list}
            stud_scelto = st.selectbox("Seleziona Studente:", list(mappa_stud.keys()))
            tipo_test = st.selectbox("Tipo di Test:", [
                "Corsa 1000m (secondi)",
                "Salto in lungo da fermo (cm)",
                "Addominali in 1 minuto (ripetizioni)"
            ])
            valore = st.number_input("Risultato ottenuto (numero):", min_value=0.0, step=1.0)
            voto_calcolato = calcola_voto(tipo_test, valore)

