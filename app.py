import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime, date
import time
import random

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
if "punti_a" not in st.session_state:
    st.session_state.punti_a = 0
if "punti_b" not in st.session_state:
    st.session_state.punti_b = 0

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

        with st.expander("❓ Hai dimenticato o vuoi cambiare la password?"):
            st.markdown("""
            Per motivi di sicurezza la password docente è protetta nelle impostazioni del server:
            1. Clicca su **Manage app** (in basso a destra) e accedi con il tuo account amministratore.
            2. Vai su **Settings** (⋮) → **Secrets**.
            3. Modifica o controlla il valore accanto a `PASSWORD_DOCENTE = "..."` e clicca **Save**.
            """)

# --- AREA DOCENTE ---
elif st.session_state.ruolo == "docente":
    st.sidebar.title("📋 Menu Docente")
    menu = st.sidebar.radio("Seleziona sezione:", [
        "1. Classi e Studenti",
        "2. Certificati Medici",
        "3. Test Fisici e Voti",
        "4. Cronometro / Timer",
        "5. Tornei e Classifiche",
        "6. Bacheca Avvisi",
        "7. Squadre & Segnapunti"
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
    # 4. CRONOMETRO / TIMER
    elif menu == "4. Cronometro / Timer":
        st.header("⏱️ Cronometro & Timer Allenamento")
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.subheader("⏲️ Conto alla Rovescia")
            secondi_timer = st.number_input("Imposta secondi:", min_value=5, max_value=3600, value=60, step=5)
            if st.button("▶️ Avvia Timer"):
                placeholder = st.empty()
                for s in range(int(secondi_timer), -1, -1):
                    mins, secs = divmod(s, 60)
                    placeholder.markdown(f"# ⏳ {mins:02d}:{secs:02d}")
                    time.sleep(1)
                placeholder.success("🔔 Tempo scaduto!")

        with col_t2:
            st.subheader("⏱️ Cronometro Manuale")
            if "crono_start" not in st.session_state:
                st.session_state.crono_start = None
            if st.button("🟢 Start"):
                st.session_state.crono_start = time.time()
            if st.button("🔴 Stop / Rileva Tempo"):
                if st.session_state.crono_start:
                    trascorso = round(time.time() - st.session_state.crono_start, 2)
                    st.success(f"Tempo rilevato: **{trascorso} secondi**")
                else:
                    st.warning("Premi prima Start!")

    # 5. TORNEI E CLASSIFICHE
    elif menu == "5. Tornei e Classifiche":
        st.header("🏆 Tornei e Classifiche")
        st.info("Registra i risultati delle partite o consulta la classifica generale del torneo scolastico.")
        col_tor1, col_tor2 = st.columns(2)
        with col_tor1:
            squadra_1 = st.text_input("Squadra / Classe 1:")
            punti_1 = st.number_input("Punteggio Squadra 1:", min_value=0, step=1)
        with col_tor2:
            squadra_2 = st.text_input("Squadra / Classe 2:")
            punti_2 = st.number_input("Punteggio Squadra 2:", min_value=0, step=1)

        if st.button("💾 Registra Risultato Partita"):
            if squadra_1 and squadra_2:
                try:
                    supabase.table("tornei").insert({
                        "squadra_a": squadra_1.strip(),
                        "squadra_b": squadra_2.strip(),
                        "punti_a": int(punti_1),
                        "punti_b": int(punti_2),
                        "data_partita": str(date.today())
                    }).execute()
                    st.success("Risultato salvato!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Errore database (verifica la tabella 'tornei'): {e}")

    # 6. BACHECA AVVISI
    elif menu == "6. Bacheca Avvisi":
        st.header("📢 Bacheca Avvisi per gli Studenti")
        titolo_avviso = st.text_input("Titolo dell'avviso:")
        testo_avviso = st.text_area("Messaggio:")
        if st.button("📤 Pubblica Avviso"):
            if titolo_avviso and testo_avviso:
                try:
                    supabase.table("avvisi").insert({
                        "titolo": titolo_avviso.strip(),
                        "messaggio": testo_avviso.strip(),
                        "data_pubblicazione": str(date.today())
                    }).execute()
                    st.success("Avviso pubblicato!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Errore nella pubblicazione: {e}")

        st.divider()
        st.subheader("Avvisi Pubblicati")
        try:
            avvisi_list = supabase.table("avvisi").select("*").order("id", desc=True).execute().data
            for avv in avvisi_list:
                with st.expander(f"📌 {avv.get('titolo', 'Avviso')} ({avv.get('data_pubblicazione', '')})"):
                    st.write(avv.get("messaggio", ""))
                    if st.button("🗑️ Elimina", key=f"del_avv_{avv['id']}"):
                        supabase.table("avvisi").delete().eq("id", avv["id"]).execute()
                        st.rerun()
        except Exception:
            st.info("Nessun avviso presente.")

    # 7. SQUADRE & SEGNAPUNTI
    elif menu == "7. Squadre & Segnapunti":
        st.header("⚽ Generatore Squadre & Segnapunti Live")

        tab_sq, tab_seg = st.tabs(["🎲 Crea Squadre Casuali", "🔢 Segnapunti Live"])

        with tab_sq:
            st.subheader("Genera Squadre da una Classe")
            classi_data = supabase.table("classi").select("*").execute().data
            if not classi_data:
                st.warning("Nessuna classe disponibile.")
            else:
                mappa_classi = {c["nome"]: c["id"] for c in classi_data}
                classe_sel = st.selectbox("Seleziona la classe:", list(mappa_classi.keys()), key="sq_classe")
                studenti_classe = supabase.table("studenti").select("nome, cognome").eq("classe_id", mappa_classi[classe_sel]).execute().data

                if studenti_classe:
                    nomi_studenti = [f"{s['cognome']} {s['nome']}" for s in studenti_classe]
                    presenti = st.multiselect("Seleziona gli studenti presenti oggi:", nomi_studenti, default=nomi_studenti)
                    num_squadre = st.number_input("Numero di squadre da creare:", min_value=2, max_value=8, value=2, step=1)

                    if st.button("🎲 Genera Squadre"):
                        if len(presenti) >= num_squadre:
                            lista_mescolata = presenti.copy()
                            random.shuffle(lista_mescolata)
                            squadre = [lista_mescolata[i::int(num_squadre)] for i in range(int(num_squadre))]
                            cols = st.columns(int(num_squadre))
                            for idx, sq in enumerate(squadre):
                                with cols[idx]:
                                    st.markdown(f"### Squadra {idx + 1}")
                                    for giocatore in sq:
                                        st.write(f"- {giocatore}")
                        else:
                            st.warning("Seleziona almeno tanti studenti quante sono le squadre!")
                else:
                    st.info("Nessuno studente registrato in questa classe.")

        with tab_seg:
            st.subheader("Segnapunti Rapido")
            col_a, col_b = st.columns(2)
            with col_a:
                nome_a = st.text_input("Nome Squadra A:", value="Squadra A")
                st.markdown(f"<h1 style='text-align: center; font-size: 72px;'>{st.session_state.punti_a}</h1>", unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                if c1.button("➕ 1 Punto A", use_container_width=True):
                    st.session_state.punti_a += 1
                    st.rerun()
                if c2.button("➖ 1 Punto A", use_container_width=True):
                    if st.session_state.punti_a > 0:
                        st.session_state.punti_a -= 1
                        st.rerun()

            with col_b:
                nome_b = st.text_input("Nome Squadra B:", value="Squadra B")
                st.markdown(f"<h1 style='text-align: center; font-size: 72px;'>{st.session_state.punti_b}</h1>", unsafe_allow_html=True)
                c3, c4 = st.columns(2)
                if c3.button("➕ 1 Punto B", use_container_width=True):
                    st.session_state.punti_b += 1
                    st.rerun()
                if c4.button("➖ 1 Punto B", use_container_width=True):
                    if st.session_state.punti_b > 0:
                        st.session_state.punti_b -= 1
                        st.rerun()

            st.divider()
            if st.button("🔄 Azzera Punteggi", use_container_width=True):
                st.session_state.punti_a = 0
                st.session_state.punti_b = 0
                st.rerun()

# --- AREA STUDENTI ---
elif st.session_state.ruolo == "studente":
    stud = st.session_state.studente_corrente
    st.sidebar.title(f"🎓 Ciao, {stud['nome']}!")
    if st.sidebar.button("🚪 Esci (Logout)"):
        st.session_state.ruolo = None
        st.session_state.studente_corrente = None
        st.rerun()

    st.title(f"🏃‍♂️ Area Personale - {stud['nome']} {stud['cognome']}")
    classe_nome = stud["classi"]["nome"] if stud.get("classi") else "N/D"
    st.markdown(f"**Classe:** {classe_nome} | **Scadenza Certificato Medico:** {stud['scadenza_certificato']}")

    st.divider()
    st.subheader("📊 I tuoi Test Fisici e Voti")
    try:
        miei_test = supabase.table("test_fisici").select("*").eq("studente_id", stud["id"]).execute().data
        if miei_test:
            st.dataframe(pd.DataFrame(miei_test)[["data_test", "tipo_test", "risultato", "voto"]], use_container_width=True)
        else:
            st.info("Nessun test fisico registrato al momento.")
    except Exception:
        st.info("Nessun risultato disponibile.")

    st.divider()
    st.subheader("📢 Bacheca Avvisi")
    try:
        avvisi = supabase.table("avvisi").select("*").order("id", desc=True).execute().data
        if avvisi:
            for a in avvisi:
                st.info(f"**{a.get('titolo', '')}** ({a.get('data_pubblicazione', '')})\n\n{a.get('messaggio', '')}")
        else:
            st.write("Nessun avviso pubblicato.")
    except Exception:
        st.write("Nessun avviso pubblicato.")
