import streamlit as st
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import os
import json
import uuid

# Configurazione della pagina Streamlit
st.set_page_config(layout="wide", page_title="Piattaforma Screening - Misuriamoci")

# Path e Credenziali Kobo
DATA_FILE = "database_misuriamoci_persistente.csv"
USERS_FILE = "utenti_db.json"

KOBO_TOKEN = "6a1f13e6c6833e0b213b3c34a171f3f2ab785833"
FORM_ID = "MWb6A71g"
URL_LETTURA = f"https://eu.kobotoolbox.org/api/v2/assets/{FORM_ID}/data.json?limit=10000"
URL_SUBMISSION = "https://eu.kobotoolbox.org/submission"
URL_FORM_WEB = "https://ee-eu.kobotoolbox.org/x/MWb6A71g"

COLONNE_PRIVACY = [
    'nome', 'cognome', 'nome e cognome', 'nome_e_cognome', 
    'email', 'indirizzo_email', 'indirizzo email', 
    'telefono', 'contatto_telefonico', 'contatto telefonico', 'cellulare'
]

# =========================================================
# 1. FUNZIONI DI GESTIONE DATI E PERSISTENZA
# =========================================================
def carica_database_locale():
    if os.path.exists(DATA_FILE):
        try:
            return pd.read_csv(DATA_FILE)
        except:
            return pd.DataFrame()
    return pd.DataFrame()

def salva_database_locale(df):
    df.to_csv(DATA_FILE, index=False)

def scarica_dati_kobo():
    headers = {"Authorization": f"Token {KOBO_TOKEN}"}
    try:
        response = requests.get(URL_LETTURA, headers=headers, timeout=5)
        if response.status_code == 200:
            results = response.json().get('results', [])
            if results:
                return pd.DataFrame(results)
    except:
        pass
    return pd.DataFrame()

def ottieni_database_completo():
    df_loc = carica_database_locale()
    df_kob = scarica_dati_kobo()
    
    if df_loc.empty and df_kob.empty:
        return pd.DataFrame()
    if df_loc.empty:
        return df_kob
    if df_kob.empty:
        return df_loc
    
    df_unito = pd.concat([df_loc, df_kob], ignore_index=True)
    cols_check = [c for c in ['Data_Misuriamoci', 'Et', 'Sesso', 'Peso', 'Altezza', 'Glicemia', 'Colesterolo', 'Trigliceridi', Uricemia'] if c in df_unito.columns]
    if cols_check:
        df_unito = df_unito.drop_duplicates(subset=cols_check, keep='last').reset_index(drop=True)
    return df_unito

def invia_singola_scheda_a_kobo(dati_dict):
    """Invia un singolo record generato dall'app direttamente alle API di Kobo Cloud"""
    headers = {"Authorization": f"Token {KOBO_TOKEN}"}
    xml_data = f'<data id="{FORM_ID}">'
    for k, v in dati_dict.items():
        if pd.notna(v) and str(v).strip() != "":
            tag = str(k).replace(" ", "_").replace("/", "_").replace("-", "_")
            xml_data += f'<{tag}>{v}</{tag}>'
    
    uid_univoco = f"uuid:{uuid.uuid4()}"
    xml_data += f'<meta><instanceID>{uid_univoco}</instanceID></meta></data>'
    
    files = {'xml_submission_file': ('submission.xml', xml_data, 'text/xml')}
    try:
        res = requests.post(URL_SUBMISSION, headers=headers, files=files, timeout=8)
        return res.status_code in [200, 201, 202]
    except:
        return False

def carica_utenti():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {
        "admin": {
            "password": "misuriamoci2026",
            "nome": "Amministratore Campagna",
            "email": "admin@misuriamoci.it",
            "ruolo": "Admin",
            "attivo": True
        },
        "operatore1": {
            "password": "volontariocri",
            "nome": "Operatore Campo",
            "email": "operatore1@cri.it",
            "ruolo": "Operatore",
            "attivo": True
        }
    }

def salva_utenti(utenti_dict):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(utenti_dict, f, ensure_ascii=False, indent=4)

st.session_state['utenti_db'] = carica_utenti()

# =========================================================
# 2. GESTIONE AUTENTICAZIONE UTENTI
# =========================================================
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_info' not in st.session_state:
    st.session_state['user_info'] = None

def mostra_login():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(
            '<div style="background: linear-gradient(135deg, #d32f2f, #ef5350); color: white; padding: 20px; text-align: center; border-radius: 8px; margin-bottom: 20px;">'
            '<h2 style="margin:0;">Accesso Riservato - Misuriamoci</h2>'
            '<p style="margin:5px 0 0 0; opacity: 0.9;">Inserisci le credenziali autorizzate per accedere al database</p>'
            '</div>', 
            unsafe_allow_html=True
        )
        
        username_input = st.text_input("Username / Utente")
        password_input = st.text_input("Password", type="password")
        
        if st.button("🔓 Accedi alla Piattaforma", use_container_width=True):
            user = st.session_state['utenti_db'].get(username_input.strip())
            if user and user['password'] == password_input.strip():
                if user['attivo']:
                    st.session_state['logged_in'] = True
                    st.session_state['user_info'] = user
                    st.session_state['username'] = username_input.strip()
                    st.success("Accesso effettuato con successo!")
                    st.rerun()
                else:
                    st.error("Il tuo account è stato disabilitato dall'amministratore.")
            else:
                st.error("Username o password non corretti.")

if not st.session_state['logged_in']:
    mostra_login()
    st.stop()

# =========================================================
# 3. INTESTAZIONE UTENTE
# =========================================================
user_curr = st.session_state['user_info']

col_h1, col_h2 = st.columns([4, 1])
with col_h1:
    st.markdown(
        f'<div style="background: linear-gradient(135deg, #d32f2f, #ef5350); color: white; padding: 15px 25px; border-radius: 8px; margin-bottom: 15px;">'
        f'<h2 style="margin:0;">Campagna "Misuriamoci"</h2>'
        f'<p style="margin:2px 0 0 0; opacity: 0.9;">Utente collegato: <b>{user_curr["nome"]}</b> ({user_curr["ruolo"]})</p>'
        f'</div>', 
        unsafe_allow_html=True
    )

with col_h2:
    st.write("")
    if st.button("🚪 Disconnetti (Logout)", use_container_width=True):
        st.session_state['logged_in'] = False
        st.session_state['user_info'] = None
        st.rerun()

df_attuale = ottieni_database_completo()

# =========================================================
# 4. SCHEDE APPLICAZIONE
# =========================================================
elenco_schede = ["📊 Archivio Screening & Grafici", "📝 Compila Nuovo Form (Diretto)", "📥 Importa Excel Storico"]

if user_curr['ruolo'] == "Admin":
    elenco_schede.append("⚙️ Gestione Accessi Utenti")

tabs = st.tabs(elenco_schede)

tab_visualizza = tabs[0]
tab_compila = tabs[1]
tab_importa = tabs[2]
tab_admin = tabs[3] if user_curr['ruolo'] == "Admin" else None

# --- SCHEDA 1: ARCHIVIO SCREENING & DASHBOARD ANALITICA ---
with tab_visualizza:
    col_t1, col_t2 = st.columns([3, 1])
    with col_t1:
        st.subheader("Database Centrale Screening")
    with col_t2:
        if st.button("🔄 Sincronizza Dati", use_container_width=True):
            st.rerun()
    
    if not df_attuale.empty:
        col_tabella, col_grafico = st.columns([3, 2])
        
        with col_tabella:
            st.write(f"### Record totali salvati nel database: **{len(df_attuale)}**")
            st.dataframe(df_attuale, use_container_width=True)
            
            if user_curr['ruolo'] == "Admin":
                st.write("---")
                st.markdown("#### 🗑️ Gestione ed Eliminazione Singola Scheda")
                
                opzioni_soggetti = []
                for idx, r in df_attuale.iterrows():
                    data_str = str(r.get('Data_Misuriamoci', r.get('Data', ''))).strip()
                    eta_s = str(r.get('Et', r.get('Eta', 'N/D'))).strip()
                    sesso_s = str(r.get('Sesso', 'N/D')).strip()
                    opzioni_soggetti.append(f"Scheda ID {idx} - Data: {data_str} ({sesso_s}, {eta_s} anni)")
                
                soggetto_da_cancellare = st.selectbox("Seleziona la scheda da rimuovere dal database:", opzioni_soggetti)
                
                if st.button("❌ Elimina Definitivamente Questa Scheda"):
                    idx_target = int(soggetto_da_cancellare.split(" - ")[0].replace("Scheda ID ", ""))
                    df_nuovo = df_attuale.drop(idx_target).reset_index(drop=True)
                    salva_database_locale(df_nuovo)
                    st.success("Scheda eliminata con successo!")
                    st.rerun()

                st.write("---")
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_attuale.to_excel(writer, index=False, sheet_name='Dati_Screening')
                excel_data = output.getvalue()
                
                st.download_button(
                    label="📥 Esporta Database Completo Pulito (.xlsx)",
                    data=excel_data,
                    file_name="database_screening_misuriamoci.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            
        with col_grafico:
            st.write("### Profilo Stili di Vita (Grafico Radar)")
            
            lista_soggetti_radar = ["-- Ultimo Inserimento Valido --"]
            for idx, r in df_attuale.iterrows():
                data_s = str(r.get('Data_Misuriamoci', r.get('Data', ''))).strip()
                eta_s = str(r.get('Et', r.get('Eta', 'N/D'))).strip()
                sesso_s = str(r.get('Sesso', 'N/D')).strip()
                lista_soggetti_radar.append(f"ID {idx}: {sesso_s}, {eta_s} anni [{data_s}]")
            
            scelta_soggetto = st.selectbox("🎯 Scegli il cittadino da visualizzare sul radar:", lista_soggetti_radar)
            
            if scelta_soggetto == "-- Ultimo Inserimento Valido --":
                df_validi = df_attuale[
                    df_attuale['Alimentazione'].notna() & 
                    (df_attuale['Alimentazione'].astype(str).str.strip() != '') &
                    (df_attuale['Alimentazione'].astype(str).str.lower() != 'none')
                ] if 'Alimentazione' in df_attuale.columns else pd.DataFrame()
                
                riga_radar = df_validi.iloc[-1] if not df_validi.empty else df_attuale.iloc[-1]
            else:
                idx_scelto = int(scelta_soggetto.split(":")[0].replace("ID ", ""))
                riga_radar = df_attuale.loc[idx_scelto]

            categories = ["Alimentazione", "Attivita_fisica", "Alcool", "Tabacco_e_cig", "Benessere_percepito", "Qualita_del_sonno"]
            labels_grafico = ["Alimentazione", "Attività Fisica", "Alcool", "Tabacco/Cig", "Benessere", "Sonno"]
            
            def pulisci_punteggio(valore):
                if pd.isna(valore) or str(valore).strip() == '' or str(valore).lower() == 'none':
                    return -1.0
                try:
                    v = float(valore)
                    return v if v in [-1.0, 1.0, 2.0, 3.0] else -1.0
                except:
                    return -1.0

            try:
                values = [pulisci_punteggio(riga_radar.get(cat)) for cat in categories]
                values = np.append(values, values[0])
                
                angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False)
                angles = np.append(angles, angles[0])
                
                grid_levels = [-1, 1, 2, 3]
                
                fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
                fig.patch.set_facecolor('white')
                ax.set_facecolor('white')
                
                ax.set_theta_offset(np.pi / 2)
                ax.set_theta_direction(-1)
                
                ax.spines['polar'].set_visible(False)
                ax.yaxis.grid(False)
                
                for r in grid_levels:
                    line_color = 'green' if r == 3 else 'gray'
                    line_width = 1.5 if r == 3 else 0.6
                    line_style = '-' if r == 3 else '--'
                    ax.plot(angles, [r] * len(angles), color=line_color, linewidth=line_width, linestyle=line_style, zorder=1)
                
                ax.set_yticks(grid_levels)
                ax.set_yticklabels(['-1', '1', '2', '3'], fontsize=9, color='darkgreen', fontweight='bold')
                
                ax.set_rlabel_position(30) 
                ax.set_ylim(-1, 3)
                
                ax.set_xticks(angles[:-1])
                ax.set_xticklabels(labels_grafico, fontsize=10, color='black', fontweight='bold')
                ax.tick_params(pad=12)
                
                ax.plot(angles, values, color='#d32f2f', linewidth=2.5, zorder=3)
                ax.fill(angles, values, color='#d32f2f', alpha=0.25, zorder=2)
                ax.scatter(angles, values, color='#d32f2f', s=45, zorder=4)
                
                plt.tight_layout()
                st.pyplot(fig)
            except Exception as e_radar:
                st.info("Seleziona un soggetto con i dati degli stili di vita compilati.")

        # --- SEZIONE INTERATTIVA: COSTRUTTORE DI GRAFICI PERSONALIZZATI ---
        st.write("---")
        st.subheader("🛠️ Costruttore Grafici Personalizzato")

        df_analisi = df_attuale.copy()
        for col in df_analisi.columns:
            converted = pd.to_numeric(df_analisi[col], errors='coerce')
            if converted.notna().sum() > 0:
                df_analisi[col] = converted

        col_ctrl1, col_ctrl2, col_ctrl3 = st.columns(3)

        with col_ctrl1:
            tipo_grafico = st.selectbox(
                "1. Scegli il tipo di grafico:",
                ["Istogramma (Distribuzione)", "Boxplot (Confronto/Outlier)", "Grafico a Dispersione (Relazione 2 Variabili)"]
            )

        colonne_numeriche = [
            c for c in df_analisi.columns 
            if pd.api.types.is_numeric_dtype(df_analisi[c]) and df_analisi[c].notna().sum() > 3
        ]

        with col_ctrl2:
            var_x = st.selectbox("2. Seleziona la Variabile Principale (Asse X):", colonne_numeriche, index=0 if colonne_numeriche else 0)

        with col_ctrl3:
            dividi_sesso = st.checkbox("Dividi il grafico per Sesso (M/F)", value=True)

        fig_custom, ax_custom = plt.subplots(figsize=(8, 4))
        
        if tipo_grafico == "Istogramma (Distribuzione)":
            if dividi_sesso and 'Sesso' in df_analisi.columns:
                df_m = pd.to_numeric(df_analisi[df_analisi['Sesso'].astype(str).str.upper() == 'M'][var_x], errors='coerce').dropna()
                df_f = pd.to_numeric(df_analisi[df_analisi['Sesso'].astype(str).str.upper() == 'F'][var_x], errors='coerce').dropna()
                ax_custom.hist(df_m, alpha=0.6, label='Uomini (M)', color='#2196f3', bins=10)
                ax_custom.hist(df_f, alpha=0.6, label='Donne (F)', color='#e91e63', bins=10)
                ax_custom.legend()
            else:
                serie_clean = pd.to_numeric(df_analisi[var_x], errors='coerce').dropna()
                ax_custom.hist(serie_clean, color='#ef5350', edgecolor='white', bins=10)
            ax_custom.set_title(f"Distribuzione di {var_x}", fontsize=12, fontweight='bold')
            ax_custom.set_xlabel(var_x)
            ax_custom.set_ylabel("Frequenza")

        elif tipo_grafico == "Boxplot (Confronto/Outlier)":
            if dividi_sesso and 'Sesso' in df_analisi.columns:
                data_to_plot = []
                labels = []
                for s in ['M', 'F']:
                    vals = pd.to_numeric(df_analisi[df_analisi['Sesso'].astype(str).str.upper() == s][var_x], errors='coerce').dropna()
                    if not vals.empty:
                        data_to_plot.append(vals.values)
                        labels.append(f"Sesso {s}")
                if data_to_plot:
                    ax_custom.boxplot(data_to_plot, tick_labels=labels)
            else:
                vals = pd.to_numeric(df_analisi[var_x], errors='coerce').dropna()
                if not vals.empty:
                    ax_custom.boxplot([vals.values], tick_labels=[var_x])
            ax_custom.set_title(f"Boxplot dei valori di {var_x}", fontsize=12, fontweight='bold')

        elif tipo_grafico == "Grafico a Dispersione (Relazione 2 Variabili)":
            options_y = [c for c in colonne_numeriche if c != var_x]
            if options_y:
                var_y = st.selectbox("3. Seleziona la Seconda Variabile (Asse Y):", options_y)
                if dividi_sesso and 'Sesso' in df_analisi.columns:
                    for s, color, label in [('M', '#2196f3', 'Uomini'), ('F', '#e91e63', 'Donne')]:
                        sub = df_analisi[df_analisi['Sesso'].astype(str).str.upper() == s]
                        x_vals = pd.to_numeric(sub[var_x], errors='coerce')
                        y_vals = pd.to_numeric(sub[var_y], errors='coerce')
                        ax_custom.scatter(x_vals, y_vals, color=color, label=label, alpha=0.7, s=50)
                    ax_custom.legend()
                else:
                    x_vals = pd.to_numeric(df_analisi[var_x], errors='coerce')
                    y_vals = pd.to_numeric(df_analisi[var_y], errors='coerce')
                    ax_custom.scatter(x_vals, y_vals, color='#ef5350', alpha=0.7, s=50)
                ax_custom.set_title(f"Relazione tra {var_x} e {var_y}", fontsize=12, fontweight='bold')
                ax_custom.set_xlabel(var_x)
                ax_custom.set_ylabel(var_y)

        ax_custom.grid(True, linestyle='--', alpha=0.5)
        st.pyplot(fig_custom)

    else:
        st.info("Nessun dato presente nel database. Compila una scheda o importa un file Excel.")

# --- SCHEDA 2: INSERIMENTO DIRETTO NATIVO (SENZA IFRAME) ---
with tab_compila:
    st.subheader("📝 Compilazione Scheda Screening (Inserimento Diretto)")
    st.markdown("Inserisci i dati del cittadino: verranno inviati al **Cloud Kobo** e salvati all'istante nel database dell'app.")
    
    with st.form("form_inserimento_diretto", clear_on_submit=True):
        st.markdown("#### 1. Dati Anagrafici Sanitari")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            data_m = st.date_input("Data Screening")
        with c2:
            sesso_m = st.selectbox("Sesso", ["M", "F"])
        with c3:
            eta_m = st.number_input("Età (anni)", min_value=1, max_value=120, value=50)
        with c4:
            fumatrice_m = st.selectbox("Fumatore / E-cig", ["No", "Sì"])
            
        st.markdown("#### 2. Parametri Antropometrici e Clinici")
        cp1, cp2, cp3, cp4 = st.columns(4)
        with cp1:
            peso_m = st.number_input("Peso (kg)", min_value=20.0, max_value=250.0, value=70.0)
        with cp2:
            altezza_m = st.number_input("Altezza (cm)", min_value=80, max_value=230, value=170)
        with cp3:
            glicemia_m = st.number_input("Glicemia (mg/dl)", min_value=30, max_value=500, value=90)
        with cp4:
            colesterolo_m = st.number_input("Colesterolo (mg/dl)", min_value=50, max_value=600, value=180)
        with cp5:
        	 trigliceridi_m = st.number_input("Trigliceridi (mg/dl)", min_value=50, max_value=600, value=180)
        with cp6:
        	 uricemia_m = st.number_input("Uricemia (mg/dl)", min_value=1, max_value=20, value=10)	 
   
        cp7, cp8 = st.columns(2)
        with cp7:
            p_max_m = st.number_input("Pressione Sistemica Max (mmHg)", min_value=50, max_value=250, value=120)
        with cp8:
            p_min_m = st.number_input("Pressione Diastolica Min (mmHg)", min_value=30, max_value=150, value=80)

        st.markdown("#### 3. Punteggi Stili di Vita (Valori Radar: -1 = Non Valido, 1 = Basso, 2 = Medio, 3 = Ottimale)")
        cr1, cr2, cr3, cr4, cr5, cr6 = st.columns(6)
        with cr1:
            alim_m = st.selectbox("Alimentazione", [3, 2, 1, -1])
        with cr2:
            att_f_m = st.selectbox("Attività Fisica", [3, 2, 1, -1])
        with cr3:
            alc_m = st.selectbox("Alcool", [3, 2, 1, -1])
        with cr4:
            tab_m = st.selectbox("Tabacco/E-cig", [3, 2, 1, -1])
        with cr5:
            ben_m = st.selectbox("Benessere", [3, 2, 1, -1])
        with cr6:
            son_m = st.selectbox("Sonno", [3, 2, 1, -1])

        btn_invia_scheda = st.form_submit_button("💾 Salva e Invia a Kobo Cloud", use_container_width=True)

    if btn_invia_scheda:
        nuova_scheda = {
            "Data_Misuriamoci": str(data_m),
            "Sesso": str(sesso_m),
            "Et": str(eta_m),
            "Peso": str(peso_m),
            "Altezza": str(altezza_m),
            "Glicemia": str(glicemia_m),
            "Colesterolo": str(colesterolo_m),
            "Pressione_massima": str(p_max_m),
            "Pressione_minima": str(p_min_m),
            "Alimentazione": alim_m,
            "Attivita_fisica": att_f_m,
            "Alcool": alc_m,
            "Tabacco_e_cig": tab_m,
            "Benessere_percepito": ben_m,
            "Qualita_del_sonno": son_m
        }
        
        # 1. Salva nel file locale
        df_loc = carica_database_locale()
        df_nuovo_loc = pd.concat([df_loc, pd.DataFrame([nuova_scheda])], ignore_index=True)
        salva_database_locale(df_nuovo_loc)
        
        # 2. Invia direttamente a Kobo via API
        inviato_kobo = invia_singola_scheda_a_kobo(nuova_scheda)
        
        if inviato_kobo:
            st.success("🎉 Scheda salvata con successo sia nell'App che su Kobo Cloud!")
        else:
            st.warning("⚠️ Scheda salvata nell'App, ma non è stato possibile sincronizzarla subito con Kobo Cloud. Rimane comunque nel database!")
        st.balloons()

# --- SCHEDA 3: IMPORTAZIONE PERMANENTE EXCEL ---
with tab_importa:
    st.subheader("Caricamento ed Estensione Permanente del Database")
    st.markdown("🔒 **Protezione Dati:** I campi personali (*Nome, Cognome, Email, Telefono*) vengono **automaticamente filtrati ed esclusi**.")
    
    file_caricato = st.file_uploader("Trascina qui il file Excel con i soggetti", type=["xlsx"])
    
    if file_caricato is not None:
        try:
            df_excel = pd.read_excel(file_caricato, sheet_name=0)
            df_excel.columns = df_excel.columns.str.strip()
            
            colonne_da_mantenere = [
                c for c in df_excel.columns 
                if str(c).lower().strip() not in COLONNE_PRIVACY
            ]
            df_anonimo = df_excel[colonne_da_mantenere].copy()
            
            st.write(f"### Rilevati **{len(df_anonimo)}** soggetti nell'Excel:")
            st.dataframe(df_anonimo.astype(str), use_container_width=True)
            
            if st.button("🚀 Salva Definitivamente i Soggetti nel Database"):
                if df_attuale.empty:
                    df_unito = df_anonimo.copy()
                else:
                    df_unito = pd.concat([df_attuale, df_anonimo], ignore_index=True)
                
                cols_cliniches = [c for c in ['Data_Misuriamoci', 'Et', 'Sesso', 'Peso', 'Altezza', 'Glicemia', 'Colesterolo'] if c in df_unito.columns]
                if cols_cliniches:
                    df_unito = df_unito.drop_duplicates(subset=cols_cliniches, keep='last').reset_index(drop=True)
                
                salva_database_locale(df_unito)
                
                st.success(f"🎉 Salvati con successo {len(df_anonimo)} soggetti nel database permanente!")
                st.balloons()
                st.rerun()
                    
        except Exception as e:
            st.error(f"Errore durante l'elaborazione dell'Excel: {str(e)}")

# --- SCHEDA 4 (RISERVATA ADMIN): GESTIONE ACCESSI ED EMAIL UTENTI ---
if tab_admin is not None:
    with tab_admin:
        st.subheader("⚙️ Pannello Amministratore: Gestione Credenziali, Email e Permessi")
        
        col_u1, col_u2 = st.columns([3, 2])
        
        with col_u1:
            st.write("### Utenti Attualmente Registrati nel Sistema")
            df_utenti = pd.DataFrame.from_dict(st.session_state['utenti_db'], orient='index')
            df_utenti = df_utenti.reset_index().rename(columns={'index': 'Username'})
            
            if 'email' not in df_utenti.columns:
                df_utenti['email'] = 'Non specificata'
            
            df_utenti['Stato Accesso'] = df_utenti['attivo'].apply(lambda x: "🟢 Attivo" if x else "🔴 Disabilitato (Bloccato)")
            df_utenti_show = df_utenti[['Username', 'nome', 'email', 'ruolo', 'Stato Accesso']].copy()
            df_utenti_show.columns = ['Username', 'Nome / Ente', 'Email', 'Ruolo', 'Stato Accesso']
            st.dataframe(df_utenti_show, use_container_width=True)
            
        with col_u2:
            st.write("### ➕ Crea Nuovo Account Utente")
            nuovo_usr = st.text_input("Username (per il login)")
            nuovo_pwd = st.text_input("Password", type="password")
            nuovo_nome = st.text_input("Nome e Cognome / Ente")
            nuova_email = st.text_input("Indirizzo Email")
            nuovo_ruolo = st.selectbox("Ruolo", ["Operatore", "Admin"])
            
            if st.button("➕ Registra e Salva Utente", use_container_width=True):
                if nuovo_usr and nuovo_pwd and nuovo_nome:
                    usr_key = nuovo_usr.strip()
                    st.session_state['utenti_db'][usr_key] = {
                        "password": nuovo_pwd.strip(),
                        "nome": nuovo_nome.strip(),
                        "email": nuova_email.strip() if nuova_email else "Non specificata",
                        "ruolo": nuovo_ruolo,
                        "attivo": True
                    }
                    salva_utenti(st.session_state['utenti_db'])
                    st.success(f"Utente '{usr_key}' registrato e salvato con successo!")
                    st.rerun()
                else:
                    st.warning("Compila i campi obbligatori: Username, Password e Nome.")
                    
        st.write("---")
        st.write("### 🔒 Revoca / Ripristina Accesso a un Utente")
        
        elenco_utenti = list(st.session_state['utenti_db'].keys())
        usr_sel = st.selectbox("Seleziona l'utente di cui modificare i permessi:", elenco_utenti)
        
        if usr_sel:
            u_data = st.session_state['utenti_db'][usr_sel]
            st.info(f"Utente selezionato: **{u_data.get('nome')}** ({u_data.get('email', 'N/D')}) — Ruolo: **{u_data.get('ruolo')}**")
            
            if usr_sel == "admin":
                st.warning("L'account principale 'admin' non può essere disabilitato.")
            else:
                stato_attuale = u_data.get('attivo', True)
                nuovo_stato = st.radio(
                    "Stato dell'account:", 
                    [True, False], 
                    format_func=lambda x: "🟢 Abilitato (Può accedere)" if x else "🔴 Disabilitato (Accesso Bloccato)", 
                    index=0 if stato_attuale else 1
                )
                
                if st.button("💾 Salva Stato Accesso Utente"):
                    st.session_state['utenti_db'][usr_sel]['attivo'] = nuovo_stato
                    salva_utenti(st.session_state['utenti_db'])
                    if nuovo_stato:
                        st.success(f"Accesso ripristinato per l'utente '{usr_sel}'.")
                    else:
                        st.error(f"Accesso bloccato per l'utente '{usr_sel}'. Non potrà più accedere finché non lo riabiliti.")
                    st.rerun()