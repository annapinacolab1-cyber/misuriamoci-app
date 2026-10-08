import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import os
import json

# Configurazione della pagina Streamlit
st.set_page_config(layout=wide, page_title=Piattaforma Screening - Misuriamoci)

# Path per i salvataggi persistenti sul server
DATA_FILE = database_misuriamoci_persistente.csv
USERS_FILE = utenti_db.json

URL_FORM_WEB = httpsee-eu.kobotoolbox.orgxMWb6A71g

COLONNE_PRIVACY = [
    'nome', 'cognome', 'nome e cognome', 'nome_e_cognome', 
    'email', 'indirizzo_email', 'indirizzo email', 
    'telefono', 'contatto_telefonico', 'contatto telefonico', 'cellulare'
]

# =========================================================
# 1. FUNZIONI PER SALVATAGGIO E CARICAMENTO PERSISTENTE
# =========================================================
def carica_database_locale()
    if os.path.exists(DATA_FILE)
        try
            return pd.read_csv(DATA_FILE)
        except
            return pd.DataFrame()
    return pd.DataFrame()

def salva_database_locale(df)
    df.to_csv(DATA_FILE, index=False)

def carica_utenti()
    if os.path.exists(USERS_FILE)
        try
            with open(USERS_FILE, 'r', encoding='utf-8') as f
                return json.load(f)
        except
            pass
    # Utenti di default iniziali
    return {
        admin {
            password misuriamoci2026,
            nome Amministratore Campagna,
            ruolo Admin,
            attivo True
        },
        operatore1 {
            password volontariocri,
            nome Operatore Campo,
            ruolo Operatore,
            attivo True
        }
    }

def salva_utenti(utenti_dict)
    with open(USERS_FILE, 'w', encoding='utf-8') as f
        json.dump(utenti_dict, f, ensure_ascii=False, indent=4)

# Caricamento utenti persistente
st.session_state['utenti_db'] = carica_utenti()

# =========================================================
# 2. GESTIONE AUTENTICAZIONE UTENTI
# =========================================================
if 'logged_in' not in st.session_state
    st.session_state['logged_in'] = False
if 'user_info' not in st.session_state
    st.session_state['user_info'] = None

def mostra_login()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2
        st.markdown(
        div style=background linear-gradient(135deg, #d32f2f, #ef5350); color white; padding 20px; text-align center; border-radius 8px; margin-bottom 20px;
            h2 style='margin0;'Accesso Riservato - Misuriamocih2
            p style='margin5px 0 0 0; opacity 0.9;'Inserisci le credenziali autorizzate per accedere al databasep
        div
        , unsafe_allow_html=True)
        
        username_input = st.text_input(Username  Utente)
        password_input = st.text_input(Password, type=password)
        
        if st.button(🔓 Accedi alla Piattaforma, use_container_width=True)
            user = st.session_state['utenti_db'].get(username_input.strip())
            if user and user['password'] == password_input.strip()
                if user['attivo']
                    st.session_state['logged_in'] = True
                    st.session_state['user_info'] = user
                    st.session_state['username'] = username_input.strip()
                    st.success(Accesso effettuato con successo!)
                    st.rerun()
                else
                    st.error(Il tuo account è stato disabilitato dall'amministratore.)
            else
                st.error(Username o password non corretti.)

if not st.session_state['logged_in']
    mostra_login()
    st.stop()

# =========================================================
# 3. INTESTAZIONE ED ELEMENTI UTENTE AUTENTICATO
# =========================================================
user_curr = st.session_state['user_info']

col_h1, col_h2 = st.columns([4, 1])
with col_h1
    st.markdown(f
    div style=background linear-gradient(135deg, #d32f2f, #ef5350); color white; padding 15px 25px; border-radius 8px; margin-bottom 15px;
        h2 style='margin0;'Campagna Misuriamocih2
        p style='margin2px 0 0 0; opacity 0.9;'Utente collegato b{user_curr['nome']}b ({user_curr['ruolo']})p
    div
    , unsafe_allow_html=True)

with col_h2
    st.write()
    if st.button(🚪 Disconnetti (Logout), use_container_width=True)
        st.session_state['logged_in'] = False
        st.session_state['user_info'] = None
        st.rerun()

# Caricamento del database persistente
df_attuale = carica_database_locale()

# =========================================================
# 4. SCHEDE APPLICAZIONE
# =========================================================
elenco_schede = [📊 Archivio Screening & Grafici, 📝 Compila Nuovo Form, 📥 Importa Excel Storico]

if user_curr['ruolo'] == Admin
    elenco_schede.append(⚙️ Gestione Accessi Utenti)

tabs = st.tabs(elenco_schede)

tab_visualizza = tabs[0]
tab_compila = tabs[1]
tab_importa = tabs[2]
tab_admin = tabs[3] if user_curr['ruolo'] == Admin else None

# --- SCHEDA 1 ARCHIVIO SCREENING & DASHBOARD ANALITICA ---
with tab_visualizza
    st.subheader(Database Centrale Screening)
    
    if not df_attuale.empty
        col_tabella, col_grafico = st.columns([3, 2])
        
        with col_tabella
            st.write(f### Record totali salvati nel database {len(df_attuale)})
            st.dataframe(df_attuale, use_container_width=True)
            
            if user_curr['ruolo'] == Admin
                st.write(---)
                st.markdown(#### 🗑️ Gestione ed Eliminazione Singola Scheda)
                
                opzioni_soggetti = []
                for idx, r in df_attuale.iterrows()
                    data_str = str(r.get('Data_Misuriamoci', r.get('Data', ''))).strip()
                    eta_s = str(r.get('Et', r.get('Eta', 'ND'))).strip()
                    sesso_s = str(r.get('Sesso', 'ND')).strip()
                    opzioni_soggetti.append(fScheda ID {idx} - Data {data_str} ({sesso_s}, {eta_s} anni))
                
                soggetto_da_cancellare = st.selectbox(Seleziona la scheda da rimuovere dal database, opzioni_soggetti)
                
                if st.button(❌ Elimina Definitivamente Questa Scheda)
                    idx_target = int(soggetto_da_cancellare.split( - )[0].replace(Scheda ID , ))
                    df_nuovo = df_attuale.drop(idx_target).reset_index(drop=True)
                    salva_database_locale(df_nuovo)
                    st.success(Scheda eliminata con successo!)
                    st.rerun()

                st.write(---)
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer
                    df_attuale.to_excel(writer, index=False, sheet_name='Dati_Screening')
                excel_data = output.getvalue()
                
                st.download_button(
                    label=📥 Esporta Database Completo Pulito (.xlsx),
                    data=excel_data,
                    file_name=database_screening_misuriamoci.xlsx,
                    mime=applicationvnd.openxmlformats-officedocument.spreadsheetml.sheet
                )
            
        with col_grafico
            st.write(### Profilo Stili di Vita (Grafico Radar))
            
            lista_soggetti_radar = [-- Ultimo Inserimento Valido --]
            for idx, r in df_attuale.iterrows()
                data_s = str(r.get('Data_Misuriamoci', r.get('Data', ''))).strip()
                eta_s = str(r.get('Et', r.get('Eta', 'ND'))).strip()
                sesso_s = str(r.get('Sesso', 'ND')).strip()
                lista_soggetti_radar.append(fID {idx} {sesso_s}, {eta_s} anni [{data_s}])
            
            scelta_soggetto = st.selectbox(🎯 Scegli il cittadino da visualizzare sul radar, lista_soggetti_radar)
            
            if scelta_soggetto == -- Ultimo Inserimento Valido --
                df_validi = df_attuale[
                    df_attuale['Alimentazione'].notna() & 
                    (df_attuale['Alimentazione'].astype(str).str.strip() != '') &
                    (df_attuale['Alimentazione'].astype(str).str.lower() != 'none')
                ] if 'Alimentazione' in df_attuale.columns else pd.DataFrame()
                
                riga_radar = df_validi.iloc[-1] if not df_validi.empty else df_attuale.iloc[-1]
            else
                idx_scelto = int(scelta_soggetto.split()[0].replace(ID , ))
                riga_radar = df_attuale.loc[idx_scelto]

            categories = [Alimentazione, Attivita_fisica, Alcool, Tabacco_e_cig, Benessere_percepito, Qualita_del_sonno]
            labels_grafico = [Alimentazione, Attività Fisica, Alcool, TabaccoCig, Benessere, Sonno]
            
            def pulisci_punteggio(valore)
                if pd.isna(valore) or str(valore).strip() == '' or str(valore).lower() == 'none'
                    return -1.0
                try
                    v = float(valore)
                    return v if v in [-1.0, 1.0, 2.0, 3.0] else -1.0
                except
                    return -1.0

            try
                values = [pulisci_punteggio(riga_radar.get(cat)) for cat in categories]
                values = np.append(values, values[0])
                
                angles = np.linspace(0, 2  np.pi, len(categories), endpoint=False)
                angles = np.append(angles, angles[0])
                
                grid_levels = [-1, 1, 2, 3]
                
                fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
                fig.patch.set_facecolor('white')
                ax.set_facecolor('white')
                
                ax.set_theta_offset(np.pi  2)
                ax.set_theta_direction(-1)
                
                ax.spines['polar'].set_visible(False)
                ax.yaxis.grid(False)
                
                for r in grid_levels
                    line_color = 'green' if r == 3 else 'gray'
                    line_width = 1.5 if r == 3 else 0.6
                    line_style = '-' if r == 3 else '--'
                    ax.plot(angles, [r]  len(angles), color=line_color, linewidth=line_width, linestyle=line_style, zorder=1)
                
                ax.set_yticks(grid_levels)
                ax.set_yticklabels(['-1', '1', '2', '3'], fontsize=9, color='darkgreen', fontweight='bold')
                
                ax.set_rlabel_position(30) 
                ax.set_ylim(-1, 3)
                
                ax.set_xticks(angles[-1])
                ax.set_xticklabels(labels_grafico, fontsize=10, color='black', fontweight='bold')
                ax.tick_params(pad=12)
                
                ax.plot(angles, values, color='#d32f2f', linewidth=2.5, zorder=3)
                ax.fill(angles, values, color='#d32f2f', alpha=0.25, zorder=2)
                ax.scatter(angles, values, color='#d32f2f', s=45, zorder=4)
                
                plt.tight_layout()
                st.pyplot(fig)
            except Exception as e_radar
                st.info(Seleziona un soggetto con i dati degli stili di vita compilati.)

        # --- SEZIONE INTERATTIVA COSTRUTTORE DI GRAFICI PERSONALIZZATI ---
        st.write(---)
        st.subheader(🛠️ Costruttore Grafici Personalizzato)

        df_analisi = df_attuale.copy()
        for col in df_analisi.columns
            converted = pd.to_numeric(df_analisi[col], errors='coerce')
            if converted.notna().sum()  0
                df_analisi[col] = converted

        col_ctrl1, col_ctrl2, col_ctrl3 = st.columns(3)

        with col_ctrl1
            tipo_grafico = st.selectbox(
                1. Scegli il tipo di grafico,
                [Istogramma (Distribuzione), Boxplot (ConfrontoOutlier), Grafico a Dispersione (Relazione 2 Variabili)]
            )

        colonne_numeriche = [
            c for c in df_analisi.columns 
            if pd.api.types.is_numeric_dtype(df_analisi[c]) and df_analisi[c].notna().sum()  3
        ]

        with col_ctrl2
            var_x = st.selectbox(2. Seleziona la Variabile Principale (Asse X), colonne_numeriche, index=0 if colonne_numeriche else 0)

        with col_ctrl3
            dividi_sesso = st.checkbox(Dividi il grafico per Sesso (MF), value=True)

        fig_custom, ax_custom = plt.subplots(figsize=(8, 4))
        
        if tipo_grafico == Istogramma (Distribuzione)
            if dividi_sesso and 'Sesso' in df_analisi.columns
                df_m = pd.to_numeric(df_analisi[df_analisi['Sesso'].astype(str).str.upper() == 'M'][var_x], errors='coerce').dropna()
                df_f = pd.to_numeric(df_analisi[df_analisi['Sesso'].astype(str).str.upper() == 'F'][var_x], errors='coerce').dropna()
                ax_custom.hist(df_m, alpha=0.6, label='Uomini (M)', color='#2196f3', bins=10)
                ax_custom.hist(df_f, alpha=0.6, label='Donne (F)', color='#e91e63', bins=10)
                ax_custom.legend()
            else
                serie_clean = pd.to_numeric(df_analisi[var_x], errors='coerce').dropna()
                ax_custom.hist(serie_clean, color='#ef5350', edgecolor='white', bins=10)
            ax_custom.set_title(fDistribuzione di {var_x}, fontsize=12, fontweight='bold')
            ax_custom.set_xlabel(var_x)
            ax_custom.set_ylabel(Frequenza)

        elif tipo_grafico == Boxplot (ConfrontoOutlier)
            if dividi_sesso and 'Sesso' in df_analisi.columns
                data_to_plot = []
                labels = []
                for s in ['M', 'F']
                    vals = pd.to_numeric(df_analisi[df_analisi['Sesso'].astype(str).str.upper() == s][var_x], errors='coerce').dropna()
                    if not vals.empty
                        data_to_plot.append(vals.values)
                        labels.append(fSesso {s})
                if data_to_plot
                    ax_custom.boxplot(data_to_plot, tick_labels=labels)
            else
                vals = pd.to_numeric(df_analisi[var_x], errors='coerce').dropna()
                if not vals.empty
                    ax_custom.boxplot([vals.values], tick_labels=[var_x])
            ax_custom.set_title(fBoxplot dei valori di {var_x}, fontsize=12, fontweight='bold')

        elif tipo_grafico == Grafico a Dispersione (Relazione 2 Variabili)
            options_y = [c for c in colonne_numeriche if c != var_x]
            if options_y
                var_y = st.selectbox(3. Seleziona la Seconda Variabile (Asse Y), options_y)
                if dividi_sesso and 'Sesso' in df_analisi.columns
                    for s, color, label in [('M', '#2196f3', 'Uomini'), ('F', '#e91e63', 'Donne')]
                        sub = df_analisi[df_analisi['Sesso'].astype(str).str.upper() == s]
                        x_vals = pd.to_numeric(sub[var_x], errors='coerce')
                        y_vals = pd.to_numeric(sub[var_y], errors='coerce')
                        ax_custom.scatter(x_vals, y_vals, color=color, label=label, alpha=0.7, s=50)
                    ax_custom.legend()
                else
                    x_vals = pd.to_numeric(df_analisi[var_x], errors='coerce')
                    y_vals = pd.to_numeric(df_analisi[var_y], errors='coerce')
                    ax_custom.scatter(x_vals, y_vals, color='#ef5350', alpha=0.7, s=50)
                ax_custom.set_title(fRelazione tra {var_x} e {var_y}, fontsize=12, fontweight='bold')
                ax_custom.set_xlabel(var_x)
                ax_custom.set_ylabel(var_y)

        ax_custom.grid(True, linestyle='--', alpha=0.5)
        st.pyplot(fig_custom)

    else
        st.info(Nessun dato presente nel database. Vai alla scheda 'Importa Excel Storico' per caricare il tuo file.)

# --- SCHEDA 2 NUOVO INSERIMENTO DIGITALE ---
with tab_compila
    st.subheader(Inserimento Scheda in Tempo Reale)
    st.markdown(Compila la scheda direttamente da qui oppure aprila in una nuova finestra.)
    
    st.link_button(🔗 Apri il Modulo a Tutto Schermo in una Nuova Scheda, URL_FORM_WEB)
    
    iframe_form = f'''
    iframe src={URL_FORM_WEB} 
            width=100% 
            height=900px 
            style=border1px solid #ddd; border-radius8px; 
            allow=geolocation; camera; microphone
    iframe
    '''
    st.components.v1.html(iframe_form, height=920, scrolling=True)

# --- SCHEDA 3 IMPORTAZIONE PERMANENTE EXCEL ---
with tab_importa
    st.subheader(Caricamento ed Estensione Permanete del Database)
    st.markdown(🔒 Protezione Dati I campi personali (Nome, Cognome, Email, Telefono) vengono automaticamente filtrati ed esclusi.)
    
    file_caricato = st.file_uploader(Trascina qui il file Excel con i soggetti, type=[xlsx])
    
    if file_caricato is not None
        try
            df_excel = pd.read_excel(file_caricato, sheet_name=0)
            df_excel.columns = df_excel.columns.str.strip()
            
            # FILTRO PRIVACY
            colonne_da_mantenere = [
                c for c in df_excel.columns 
                if str(c).lower().strip() not in COLONNE_PRIVACY
            ]
            df_anonimo = df_excel[colonne_da_mantenere].copy()
            
            st.write(f### Rilevati {len(df_anonimo)} soggetti nell'Excel)
            st.dataframe(df_anonimo.astype(str), use_container_width=True)
            
            if st.button(🚀 Salva Definitivamente i Soggetti nel Database)
                if df_attuale.empty
                    df_unito = df_anonimo.copy()
                else
                    df_unito = pd.concat([df_attuale, df_anonimo], ignore_index=True)
                
                # De-duplicazione
                cols_cliniches = [c for c in ['Data_Misuriamoci', 'Et', 'Sesso', 'Peso', 'Altezza', 'Glicemia', 'Colesterolo'] if c in df_unito.columns]
                if cols_cliniches
                    df_unito = df_unito.drop_duplicates(subset=cols_cliniches, keep='last').reset_index(drop=True)
                
                salva_database_locale(df_unito)
                
                st.success(f🎉 Salvati con successo {len(df_anonimo)} soggetti nel database permanente!)
                st.balloons()
                st.rerun()
                    
        except Exception as e
            st.error(fErrore durante l'elaborazione dell'Excel {str(e)})

# --- SCHEDA 4 (RISERVATA ADMIN) GESTIONE ACCESSI UTENTI PERSISTENTE ---
if tab_admin is not None
    with tab_admin
        st.subheader(⚙️ Pannello Amministratore Gestione Credenziali e Permessi)
        
        col_u1, col_u2 = st.columns([2, 1])
        
        with col_u1
            st.write(### Utenti Attualmente Registrati)
            df_utenti = pd.DataFrame.from_dict(st.session_state['utenti_db'], orient='index')
            df_utenti = df_utenti.reset_index().rename(columns={'index' 'Username'})
            df_utenti_show = df_utenti[['Username', 'nome', 'ruolo', 'attivo']].copy()
            st.dataframe(df_utenti_show, use_container_width=True)
            
        with col_u2
            st.write(### ➕ Aggiungi Nuovo Utente)
            nuovo_usr = st.text_input(Nuovo Username)
            nuovo_pwd = st.text_input(Nuova Password, type=password)
            nuovo_nome = st.text_input(Nome e Cognome  Ente)
            nuovo_ruolo = st.selectbox(Ruolo, [Operatore, Admin])
            
            if st.button(Crea Account Utente, use_container_width=True)
                if nuovo_usr and nuovo_pwd and nuovo_nome
                    usr_key = nuovo_usr.strip()
                    st.session_state['utenti_db'][usr_key] = {
                        password nuovo_pwd.strip(),
                        nome nuovo_nome.strip(),
                        ruolo nuovo_ruolo,
                        attivo True
                    }
                    salva_utenti(st.session_state['utenti_db'])
                    st.success(fUtente '{usr_key}' registrato e salvato permanentemente!)
                    st.rerun()
                else
                    st.warning(Compila tutti i campi obbligatori.)
                    
        st.write(---)
        st.write(### 🔒 Revoca  Abilita Accesso Utente)
        usr_sel = st.selectbox(Seleziona utente da gestire, list(st.session_state['utenti_db'].keys()))
        if usr_sel != admin
            stato_attuale = st.session_state['utenti_db'][usr_sel]['attivo']
            nuovo_stato = st.radio(Stato Account, [True, False], format_func=lambda x Abilitato (Attivo) if x else Disabilitato (Bloccato), index=0 if stato_attuale else 1)
            if st.button(Salva Stato Utente)
                st.session_state['utenti_db'][usr_sel]['attivo'] = nuovo_stato
                salva_utenti(st.session_state['utenti_db'])
                st.success(Permessi aggiornati e salvati!)
                st.rerun()