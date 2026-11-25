import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime, date
import time
import random
import string
from itertools import combinations

st.set_page_config(page_title="MotoriaPro • Portale Educazione Fisica", page_icon="🏅", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #F4F7FA; }
    .hero-banner {
        background: linear-gradient(135deg, #0052CC 0%, #0747A6 100%);
        padding: 24px 28px;
        border-radius: 16px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 8px 20px rgba(0, 82, 204, 0.18);
    }
    .hero-banner h1 { color: white !important; margin: 0; font-size: 2rem; font-weight: 800; }
    .hero-banner p { color: #DEEBFF; margin: 6px 0 0 0; font-size: 1rem; }
    .stButton > button {
        border-radius: 12px;
        font-weight: 700;
        padding: 0.65rem 1.2rem;
        border: none;
        box-shadow: 0 3px 8px rgba(0,0,0,0.08);
    }
    .score-card {
        background: #FFFFFF;
        border-radius: 18px;
        padding: 24px;
        text-align: center;
        border-top: 6px solid #0052CC;
        box-shadow: 0 6px 18px rgba(15, 23, 42, 0.07);
        color: #0F172A;
    }
    .match-card {
        background-color: #FFFFFF;
        border-left: 6px solid #FF6B00;
        padding: 14px 18px;
        border-radius: 12px;
        margin-bottom: 10px;
        color: #1E293B;
        box-shadow: 0 3px 10px rgba(15, 23, 42, 0.05);
    }
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E2E8F0;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

def genera_codice_sicuro():
    numeri = ''.join(random.choices(string.digits, k=4))
    lettere = ''.join(random.choices(string.ascii_uppercase, k=2))
    return f"MTR-{numeri}-{lettere}"

def calcola_voto(tipo_test, valore):
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
    tutte_coppie = list(combinations(squadre, 2))
    random.shuffle(tutte_coppie)
    conteggio = {s: 0 for s in squadre}
    partite_scelte = []

    for _ in range(len(tutte_coppie) * 2):
        if max_partite_totali and len(partite_scelte) >= max_partite_totali:
            break
        candidati = [
            c for c in tutte_coppie
            if c not in partite_scelte
            and conteggio[c[0]] < partite_per_squadra
            and conteggio[c[1]] < partite_per_squadra
        ]
        if not candidati:
            break
        candidati.sort(key=lambda c: conteggio[c[0]] + conteggio[c[1]])
        scelta = candidati[0]
        partite_scelte.append(scelta)
        conteggio[scelta[0]] += 1
        conteggio[scelta[1]] += 1

    return partite_scelte, conteggio

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

if st.session_state.ruolo is None:
    st.markdown("""
    <div class="hero-banner">
        <h1>🏅 MotoriaPro • Educazione Fisica</h1>
        <p>Gestione classi, certificati medici, test fisici e tornei scolastici in un unico posto</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.subheader("🎓 Area Studenti")
            codice_input = st.text_input("Codice Personale Studente:", type="password", placeholder="Es. MTR-4821-XK")
            if st.button("Entra come Studente", type="primary", use_container_width=True):
                res = supabase.table("studenti").select("*, classi(nome)").eq("codice_personale", codice_input.strip()).execute()
                if res.data:
                    st.session_state.ruolo = "studente"
                    st.session_state.studente_corrente = res.data[0]
                    st.rerun()
                else:
                    st.error("Codice personale non valido.")

    with col2:
        with st.container(border=True):
            st.subheader("📋 Area Docente")
            pwd_input = st.text_input("Password Docente:", type="password")
            if st.button("Entra come Docente", type="primary", use_container_width=True):
                if pwd_input == st.secrets["PASSWORD_DOCENTE"]:
                    st.session_state.ruolo = "docente"
                    st.rerun()
                else:
                    st.error("Password errata.")

    with st.expander("🔑 Password o Codice dimenticato?"):
        tab_rec_stud, tab_rec_doc = st.tabs(["🎓 Recupero Studente", "📋 Recupero Docente"])
        with tab_rec_stud:
            st.info(
                "**Hai smarrito il tuo Codice Personale?**\n\n"
                "Per tutelare la privacy dei minori (GDPR), i codici non vengono inviati via email. "
                "Chiedi direttamente al tuo **docente di Educazione Fisica**: potrà consultarlo o generartene uno nuovo in pochi secondi."
            )
        with tab_rec_doc:
            st.write("Inserisci il **Codice PUK di emergenza** per recuperare la password docente:")
            puk_input = st.text_input("Codice PUK di Emergenza:", type="password", key="puk_rec")
            if st.button("Verifica PUK", key="btn_puk"):
                codice_puk = st.secrets.get("PUK_DOCENTE", "PUK2026")
                if puk_input == codice_puk:
                    st.success(f"✅ Identità verificata! La password docente attuale è: **{st.secrets['PASSWORD_DOCENTE']}**")
                else:
                    st.error("Codice PUK non valido.")

    with st.expander("🔒 Informativa Sicurezza & Privacy Minori (GDPR)"):
        st.info("• **Tutela Dati Minori:** Codici casuali anti-indovinamento.\n• **Accesso Biometrico:** Compatibile con Face ID / Impronta del telefono.")

elif st.session_state.ruolo == "docente":
    st.sidebar.title("🏅 MotoriaPro")
    menu = st.sidebar.radio("Seleziona sezione:", [
        "1. Classi e Studenti",
        "2. Certificati Medici",
        "3. Test Fisici e Voti",
        "4. Cronometro / Timer",
        "5. Tornei & Generatore Partite",
        "6. Bacheca Avvisi",
        "7. Squadre & Segnapunti"
    ])
    if st.sidebar.button("🚪 Esci (Logout)", use_container_width=True):
        st.session_state.ruolo = None
        st.rerun()

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
                        time.sleep(0.5)
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
                c_cod1, c_cod2 = st.columns(2)
                codice = c_cod1.text_input("Codice Privacy Studente:", value=st.session_state.codice_generato)
                if c_cod2.button("🔄 Nuovo Codice", use_container_width=True):
                    st.session_state.codice_generato = genera_codice_sicuro()
                    st.rerun()
                scad_cert = st.date_input("Scadenza Certificato Medico:", value=date.today())
                note = st.text_area("Note riservate docente:")

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
                            time.sleep(0.5)
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
                        supabase.table("studenti").delete().eq("id", mappa_del_stud[stud_da_elim]).execute()
                        st.success("Studente eliminato!")
                        time.sleep(0.5)
                        st.rerun()
                else:
                    st.info("Nessuno studente presente.")

            with col_del2:
                st.subheader("Elimina Classe")
                classi_del_list = supabase.table("classi").select("*").execute().data
                if classi_del_list:
                    mappa_del_classi = {c["nome"]: c["id"] for c in classi_del_list}
                    classe_da_elim = st.selectbox("Scegli classe:", list(mappa_del_classi.keys()))
                    if st.button("🗑️ Elimina Classe", type="primary"):
                        supabase.table("classi").delete().eq("id", mappa_del_classi[classe_da_elim]).execute()
                        st.success("Classe eliminata!")
                        time.sleep(0.5)
                        st.rerun()
                else:
                    st.info("Nessuna classe presente.")
        st.divider()
        st.subheader("Elenco Studenti Registrati")
        studenti_list = supabase.table("studenti").select("nome, cognome, codice_personale, scadenza_certificato, note, classi(nome)").execute().data
        if studenti_list:
            df = pd.DataFrame([{
                "Classe": s["classi"]["nome"] if s["classi"] else "",
                "Cognome": s["cognome"],
                "Nome": s["nome"],
                "Codice Privacy": s["codice_personale"],
                "Scadenza Certificato": s["scadenza_certificato"],
                "Note": s["note"]
            } for s in studenti_list])
            st.dataframe(df, use_container_width=True)

    elif menu == "2. Certificati Medici":
        st.header("🩺 Controllo Scadenze Certificati Medici")
        studenti_list = supabase.table("studenti").select("id, nome, cognome, scadenza_certificato, classi(nome)").execute().data
        if not studenti_list:
            st.info("Nessuno studente registrato.")
        else:
            oggi = date.today()
            for s in studenti_list:
                scad = datetime.strptime(s["scadenza_certificato"], "%Y-%m-%d").date()
                giorni = (scad - oggi).days
                classe_nome = s["classi"]["nome"] if s["classi"] else ""
                if giorni < 0:
                    st.error(f"❌ **{s['cognome']} {s['nome']}** ({classe_nome}) — SCADUTO il {scad.strftime('%d/%m/%Y')}")
                elif giorni <= 30:
                    st.warning(f"⚠️ **{s['cognome']} {s['nome']}** ({classe_nome}) — In scadenza tra {giorni} giorni ({scad.strftime('%d/%m/%Y')})")
                else:
                    st.success(f"✅ **{s['cognome']} {s['nome']}** ({classe_nome}) — Valido fino al {scad.strftime('%d/%m/%Y')}")

    elif menu == "3. Test Fisici e Voti":
        st.header("⏱️ Registrazione Test Fisici e Calcolo Voti")
        studenti_list = supabase.table("studenti").select("id, nome, cognome, classi(nome)").execute().data
        if not studenti_list:
            st.warning("Nessuno studente registrato.")
        else:
            mappa_stud = {f"{s['cognome']} {s['nome']} ({s['classi']['nome'] if s['classi'] else ''})": s["id"] for s in studenti_list}
            stud_scelto = st.selectbox("Seleziona Studente:", list(mappa_stud.keys()))
            tipo_test = st.selectbox("Tipo di Test:", [
                "Corsa 1000m (secondi)",
                "Salto in lungo da fermo (cm)",
                "Addominali in 1 minuto (ripetizioni)"
            ])
            valore = st.number_input("Risultato ottenuto (numero):", min_value=0.0, step=1.0)
            voto_calcolato = calcola_voto(tipo_test, valore)
            st.info(f"📊 Voto calcolato automaticamente: **{voto_calcolato}**")

            if st.button("Registra Risultato", type="primary"):
                supabase.table("risultati_test").insert({
                    "studente_id": mappa_stud[stud_scelto],
                    "tipo_test": tipo_test,
                    "valore": valore,
                    "voto": voto_calcolato
                }).execute()
                st.success("Risultato e voto salvati!")

    elif menu == "4. Cronometro / Timer":
        st.header("⏱️ Timer per Circuiti e Prove")
        secondi = st.number_input("Imposta durata Timer (secondi):", min_value=5, max_value=3600, value=30, step=5)
        if st.button("▶️ Avvia Countdown", type="primary"):
            placeholder = st.empty()
            for t in range(int(secondi), -1, -1):
                mins, secs = divmod(t, 60)
                placeholder.markdown(f"<h1 style='text-align: center; font-size: 85px; color: #0052CC;'>{mins:02d}:{secs:02d}</h1>", unsafe_allow_html=True)
                time.sleep(1)
            st.balloons()
            st.success("Tempo scaduto!")

    elif menu == "5. Tornei & Generatore Partite":
        st.header("🏆 Tornei Scolastici e Generatore Partite")
        tab_gen, tab_class = st.tabs(["📅 Generatore Torneo all'Italiana", "📊 Classifica Pubblica"])

        with tab_gen:
            st.subheader("Generatore Automatico Abbinamenti")
            classi_db = supabase.table("classi").select("nome").execute().data
            nomi_db = [c["nome"] for c in classi_db]

            usa_db = st.checkbox("Usa le classi già salvate nel database", value=bool(nomi_db))
            if usa_db and nomi_db:
                squadre_torneo = st.multiselect("Seleziona le classi iscritte al torneo:", nomi_db, default=nomi_db)
            else:
                testo_squadre = st.text_area("Scrivi le classi/squadre partecipanti (una per riga o separate da virgola):", value="1A, 1B, 2A, 2B, 3A, 3B")
                squadre_torneo = [s.strip() for s in testo_squadre.replace(",", "\n").split("\n") if s.strip()]

            col_p1, col_p2 = st.columns(2)
            max_per_squadra = col_p1.number_input("Quante partite deve giocare ogni classe?", min_value=1, max_value=20, value=2, step=1)
            limita_tot = col_p2.checkbox("Imposta un tetto massimo totale di partite", value=False)
            max_totali = None
            if limita_tot:
                max_totali = col_p2.number_input("Numero massimo totale di partite da disputare:", min_value=1, max_value=100, value=6, step=1)

            if st.button("⚡ Genera Calendario Partite", type="primary", use_container_width=True):
                if len(squadre_torneo) < 2:
                    st.warning("Inserisci almeno 2 classi per generare il calendario!")
                else:
                    partite, bilancio = genera_calendario_italiana(squadre_torneo, int(max_per_squadra), int(max_totali) if max_totali else None)
                    st.success(f"Generate **{len(partite)} partite** equilibrate!")
                    for i, (sq1, sq2) in enumerate(partite, 1):
                        st.markdown(f"<div class='match-card'><b>Partita #{i}:</b> &nbsp; {sq1} &nbsp; 🆚 &nbsp; {sq2}</div>", unsafe_allow_html=True)
                    with st.expander("📋 Riepilogo partite assegnate per ciascuna classe"):
                        df_bil = pd.DataFrame([{"Classe": k, "Partite assegnate": v} for k, v in bilancio.items()])
                        st.dataframe(df_bil, use_container_width=True)

        with tab_class:
            st.subheader("Aggiorna Classifica Visibile agli Studenti")
            nome_torneo = st.text_input("Nome Torneo:")
            squadra = st.text_input("Nome Squadra / Classe:")
            punti = st.number_input("Punti in classifica:", min_value=0, step=1)
            if st.button("Salva Punteggio in Classifica", type="primary"):
                if nome_torneo and squadra:
                    supabase.table("tornei").insert({
                        "nome_torneo": nome_torneo.strip(),
                        "squadra": squadra.strip(),
                        "punti": int(punti)
                    }).execute()
                    st.success("Dati torneo salvati!")
            tornei_data = supabase.table("tornei").select("*").order("punti", desc=True).execute().data
            if tornei_data:
                st.dataframe(pd.DataFrame(tornei_data)[["nome_torneo", "squadra", "punti"]], use_container_width=True)

    elif menu == "6. Bacheca Avvisi":
        st.header("📌 Pubblica Avviso in Bacheca")
        titolo = st.text_input("Titolo Avviso:")
        messaggio = st.text_area("Testo del messaggio per gli studenti:")
        if st.button("Pubblica Avviso", type="primary"):
            if titolo and messaggio:
                supabase.table("bacheca").insert({"titolo": titolo, "messaggio": messaggio}).execute()
                st.success("Avviso pubblicato!")
    elif menu == "7. Squadre & Segnapunti":
        st.header("⚽ Strumenti Rapidi da Palestra")
        tab_pt, tab_sq = st.tabs(["🔢 Tabellone Segnapunti", "🎲 Sorteggio Squadre"])

        with tab_pt:
            col_n1, col_n2 = st.columns(2)
            nome_a = col_n1.text_input("Nome Squadra 1:", value="Squadra Casa")
            nome_b = col_n2.text_input("Nome Squadra 2:", value="Squadra Ospite")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"<div class='score-card'><h3>{nome_a}</h3><h1 style='font-size: 95px; color: #0052CC; margin: 10px 0;'>{st.session_state.punti_a}</h1></div>", unsafe_allow_html=True)
                b1, b2, b3, b4 = st.columns(4)
                if b1.button("+1", key="a1", use_container_width=True):
                    st.session_state.punti_a += 1
                    st.rerun()
                if b2.button("+2", key="a2", use_container_width=True):
                    st.session_state.punti_a += 2
                    st.rerun()
                if b3.button("+3", key="a3", use_container_width=True):
                    st.session_state.punti_a += 3
                    st.rerun()
                if b4.button("-1", key="am1", use_container_width=True):
                    st.session_state.punti_a = max(0, st.session_state.punti_a - 1)
                    st.rerun()

            with c2:
                st.markdown(f"<div class='score-card' style='border-top-color: #FF6B00;'><h3>{nome_b}</h3><h1 style='font-size: 95px; color: #FF6B00; margin: 10px 0;'>{st.session_state.punti_b}</h1></div>", unsafe_allow_html=True)
                b1, b2, b3, b4 = st.columns(4)
                if b1.button("+1", key="b1", use_container_width=True):
                    st.session_state.punti_b += 1
                    st.rerun()
                if b2.button("+2", key="b2", use_container_width=True):
                    st.session_state.punti_b += 2
                    st.rerun()
                if b3.button("+3", key="b3", use_container_width=True):
                    st.session_state.punti_b += 3
                    st.rerun()
                if b4.button("-1", key="bm1", use_container_width=True):
                    st.session_state.punti_b = max(0, st.session_state.punti_b - 1)
                    st.rerun()

            if st.button("🔄 Azzera Punteggio Partita", use_container_width=True):
                st.session_state.punti_a = 0
                st.session_state.punti_b = 0
                st.rerun()

        with tab_sq:
            st.subheader("Creazione Rapida Squadre")
            classi_data = supabase.table("classi").select("*").execute().data
            opzioni_fonte = ["Inserisci nomi manualmente"] + [f"Classe {c['nome']}" for c in classi_data]
            fonte = st.selectbox("Da dove prendo i giocatori?", opzioni_fonte)
            giocatori = []
            if fonte == "Inserisci nomi manualmente":
                nomi_raw = st.text_area("Scrivi un nome per riga (oppure separati da virgola):", placeholder="Marco\nLuca\nGiulia\nSofia...")
                if nomi_raw:
                    giocatori = [n.strip() for n in nomi_raw.replace(",", "\n").split("\n") if n.strip()]
            else:
                nome_cl = fonte.replace("Classe ", "")
                cl_id = next((c["id"] for c in classi_data if c["nome"] == nome_cl), None)
                if cl_id:
                    stud_cl = supabase.table("studenti").select("nome, cognome").eq("classe_id", cl_id).execute().data
                    tutti_nomi = [f"{s['cognome']} {s['nome']}" for s in stud_cl]
                    giocatori = st.multiselect("Seleziona gli studenti presenti oggi:", tutti_nomi, default=tutti_nomi)

            num_squadre = st.number_input("Numero di squadre da formare:", min_value=2, max_value=10, value=2, step=1)
            if st.button("🎲 Sorteggia Squadre", type="primary", use_container_width=True):
                if len(giocatori) < num_squadre:
                    st.warning("Inserisci almeno tanti giocatori quante sono le squadre!")
                else:
                    mescolati = giocatori.copy()
                    random.shuffle(mescolati)
                    cols = st.columns(int(num_squadre))
                    for idx in range(int(num_squadre)):
                        membri = mescolati[idx::int(num_squadre)]
                        with cols[idx]:
                            with st.container(border=True):
                                st.markdown(f"### Squadra {idx + 1}")
                                for m in membri:
                                    st.write(f"• {m}")

elif st.session_state.ruolo == "studente":
    stud = st.session_state.studente_corrente
    st.sidebar.title(f"👋 Ciao, {stud['nome']}!")
    st.sidebar.write(f"Classe: **{stud['classi']['nome'] if stud['classi'] else ''}**")
    if st.sidebar.button("🚪 Esci", use_container_width=True):
        st.session_state.ruolo = None
        st.session_state.studente_corrente = None
        st.rerun()

    st.title("🎓 Area Personale Studente")
    scad = datetime.strptime(stud["scadenza_certificato"], "%Y-%m-%d").date()
    if scad < date.today():
        st.error(f"⚠️ Il tuo certificato medico è SCADUTO il {scad.strftime('%d/%m/%Y')}. Ricordati di rinnovarlo!")
    else:
        st.success(f"✅ Certificato medico valido fino al {scad.strftime('%d/%m/%Y')}")

    tab1, tab2, tab3 = st.tabs(["📊 I Miei Risultati", "🏆 Classifiche Tornei", "📌 Bacheca Avvisi"])
    with tab1:
        ris = supabase.table("risultati_test").select("tipo_test, valore, voto, data_test").eq("studente_id", stud["id"]).execute().data
        if ris:
            st.dataframe(pd.DataFrame(ris), use_container_width=True)
        else:
            st.info("Nessun test fisico registrato finora.")
    with tab2:
        tornei_data = supabase.table("tornei").select("nome_torneo, squadra, punti").order("punti", desc=True).execute().data
        if tornei_data:
            st.dataframe(pd.DataFrame(tornei_data), use_container_width=True)
        else:
            st.info("Nessun torneo attivo al momento.")
    with tab3:
        avvisi = supabase.table("bacheca").select("titolo, messaggio, data_creazione").order("data_creazione", desc=True).execute().data
        for a in avvisi:
            with st.container(border=True):
                st.subheader(a["titolo"])
                st.write(a["messaggio"])
