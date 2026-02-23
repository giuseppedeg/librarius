# Librarius - Documentazione Completa

## Indice
1. [Panoramica del Progetto](#panoramica)
2. [Architettura del Sistema](#architettura)
3. [Struttura delle Cartelle](#struttura)
4. [Moduli Principali](#moduli)
5. [Flusso di Lavoro](#flusso)
6. [Installazione e Configurazione](#installazione)
7. [Utilizzo dell'Applicazione](#utilizzo)
8. [API ed Endpoint](#api)
9. [Modelli di Machine Learning](#modelli)
10. [Formati Dati](#formati)

---

## <a name="panoramica"></a>1. Panoramica del Progetto

### Descrizione Generale
**Librarius** è un software specializzato per l'assistenza nella trascrizione di documenti manoscritti. Il progetto utilizza tecniche avanzate di visione artificiale e machine learning per automatizzare il processo di riconoscimento e trascrizione di testi manoscritti.

### Funzionalità Principali
- **Segmentazione di Righe**: Suddivisione automatica del documento in righe di testo
- **Segmentazione di Parole**: Suddivisione delle righe in singole parole
- **Riconoscimento Ottico di Caratteri (HTR - Handwritten Text Recognition)**: Riconoscimento automatico del testo manoscritto
- **Interfaccia Grafica Intuitiva**: GUI web-based per la visualizzazione e correzione dei risultati
- **Gestione Dei Dizionari**: Supporto per dizionari in italiano e inglese per la correzione ortografica
- **Logging e Analisi Temporali**: Registrazione dei tempi di trascrizione per ogni parola

### Tecnologie Utilizzate
- **Python 3.x**: Linguaggio principale
- **PyQt/wxPython**: Framework per GUI (nativa)
- **Eel**: Framework per interfaccia web-based
- **PyTorch**: Framework per deep learning
- **TrOCR**: Modello transformer per riconoscimento di testo manoscritto
- **OpenCV**: Elaborazione di immagini
- **scikit-image**: Processamento avanzato di immagini
- **Anaconda**: Gestione dell'ambiente Python

---

## <a name="architettura"></a>2. Architettura del Sistema

### Componenti Principali

```
┌───────────────────────────────────────────────────────────────┐
│                    GUI Web (Eel + HTML/JS/CSS)                │
├───────────────────────────────────────────────────────────────┤
│                    corrector_business.py (Handler)            │
│                  - Gestione dello stato documenti             │
│                  - Coordinamento tra moduli                   │
├───────────────────────────────────────────────────────────────┤
│                       Toolbox (Moduli Core)                   │
│  ┌──────────────────┬──────────────────┬──────────────────┐   │
│  │ line_segmenter   │ word_segmenter   │ trocr_manager    │   │
│  │ - Segmentazione  │ - Segmentazione  │ - Riconoscimento │   │
│  │   di righe       │   di parole      │   di testo       │   │
│  └──────────────────┴──────────────────┴──────────────────┘   │
├───────────────────────────────────────────────────────────────┤
│                      Modelli Pre-addestrati                   │
│  ┌──────────────────────┬───────────────────────────────────┐ │
│  │ Line Segmenter Model │ TrOCR Model (Hugging Face)        │ │
│  │ (UNetMini)           │ (microsoft/trocr-base-handwritten)│ │
│  └──────────────────────┴───────────────────────────────────┘ │
├───────────────────────────────────────────────────────────────┤
│                      Gestione Dati                            │
│  ┌──────────────────┬──────────────────┬──────────────────┐   │
│  │ utils.py         │ configs.py       │ als_read.py      │   │
│  │ - Utility        │ - Configurazioni │ - Editor CLI     │   │
│  └──────────────────┴──────────────────┴──────────────────┘   │
└───────────────────────────────────────────────────────────────┘
```

### Flusso dei Dati

1. **Ingresso**: Documento immagine (JPG, PNG)
2. **Elaborazione**:
   - Segmentazione in righe
   - Segmentazione in parole
   - Riconoscimento di testo
3. **Output**: File .als (Alignment File) con bounding box e opzioni di trascrizione
4. **Visualizzazione**: GUI web per review e correzione

---

## <a name="struttura"></a>3. Struttura delle Cartelle

```
librarius/
├── GUI.py                          # Entry point principale
├── configs.py                      # Configurazioni globali
├── configs                         # Configurazioni globali JSON like
├── corrector_business.py           # Handler logica applicativa
├── utils.py                        # Funzioni di utility
├── image_utils.py                  # Utility per immagini
├── als_read.py                     # Editor CLI per file .als
├── predict_als.py                  # Predizione standalone
├── environment.yml                 # Configurazione ambiente Conda
│
├── toolbox/                        # Moduli core
│   ├── __init__.py
│   ├── line_segmenter.py          # Segmentazione righe
│   ├── line_segmenter_model.py    # Modello UNetMini
│   ├── word_segmenter.py          # Segmentazione parole
│   └── trocr_manager.py           # Manager del modello TrOCR
│
├── trocr/                          # Modulo TrOCR personalizzato
│   ├── __main__.py
│   ├── main.py                    # Predictor e trainer
│   ├── cli.py                     # Command line interface
│   ├── dataset.py                 # Dataset loader
│   ├── util.py                    # Utility
│   ├── context.py
│   ├── scripts.py
│   ├── configs/                   # Configurazioni TrOCR
│   └── ...
│
├── www/                            # Frontend web
│   ├── index.html                 # Pagina principale
│   ├── css/                       # Stylesheet
│   ├── js/                        # Script JavaScript
│   ├── images/                    # Immagini UI
│   └── data/                      # Dati dinamici (configs.js, keyword_list.js)
│
├── data/                           # Dati dell'applicazione
│   ├── doc_img/                   # Immagini documenti
│   ├── alignments/                # File .als (alignment)
│   ├── line_segmentation/         # Output segmentazione righe
│   ├── line_segmentation_masks/   # Maschere segmentazione
│   ├── logs/                      # Log timing trascrizioni
│   └── outs/                      # Output trascrizioni
│
├── models/                         # Modelli pre-addestrati
│   ├── line_segmenter/            # Checkpoint segmentatore righe
│   └── trocr/                     # Modelli TrOCR
│
├── dicts/                          # Dizionari
│   ├── eng                        # Dizionario inglese
│   └── ita                        # Dizionario italiano
│
├── assets/                         # Asset applicazione
│   ├── font/
│   ├── splash/
│   └── new_icon/
│
├── DOC/                           # Documentazione
└── readme.md                      # README
```

---

## <a name="moduli"></a>4. Moduli Principali

### 4.1 GUI.py - Entry Point Applicazione

**Responsabilità**:
- Inizializzazione dell'interfaccia web
- Gestione della porta e del server locale
- Binding tra backend Python e frontend JavaScript
- Logging console

**Flusso di Esecuzione**:
```
1. Setup logging stdout/stderr
2. Caricamento configurazioni
3. Inizializzazione handler (corrector_business)
4. Generazione file .js dinamici (configs.js, keyword_list.js)
5. Avvio server web Eel
6. Binding API endpoint
7. Chiusura splash screen (se PyInstaller)
```

**Funzioni Esposte (via @eel.expose)**:
- `load_document(doc)`: Carica un documento
- `release_document()`: Scarica il documento attuale
- `get_next_row_image()`: Carica riga successiva
- `get_prev_row_image()`: Carica riga precedente
- `_update_view(list_tr)`: Aggiorna UI

### 4.2 corrector_business.py - Handler Principale

**Classe Principale**: `Handeler` (nota: nome originale con typo)

**Responsabilità**:
- Gestione dello stato dell'applicazione
- Coordinamento tra moduli
- Gestione file alignment (.als)
- Gestione immagini corrente (documento, riga, parola)
- Logging tempi trascrizione

**Attributi Principali**:
- `base_folder`: Cartella base dati
- `document_img_name`: Nome immagine documento
- `als_file_path`: Path file alignment
- `alignments_file`: Struttura dati alignment (dict)
- `current_transcription`: Trascrizioni salvate
- `all_boxes`: Bounding box parole
- `all_transcripts_list`: Lista opzioni trascrizione
- `current_doc_img`, `current_row_img`, `current_word_img`: Immagini in memoria

**Metodi Principali**:
- `__init__()`: Inizializzazione
- `reinit(document)`: Carica nuovo documento
- `reinit_als()`: Ricarica file alignment
- `load_line_segmentations_info()`: Carica info segmentazione righe
- `get_currentpage_transcription()`: Ottiene trascrizione pagina corrente
- `get_currentword_transcript()`: Ottiene transcript parola corrente
- `clean()`: Pulisce risorse
- Metodi per navigazione e modifica trascrizioni

### 4.3 configs.py - Configurazioni Globali

**Contiene**:
- Costanti di configurazione applicazione
- Path relative a cartelle
- Parametri modelli
- Charset speciali (SPLIT_CH, FUSE_CH, CREATE_CH)
- Batch size e num workers

**Variabili Chiave**:
```python
PORT = 9565                    # Porta web server
MARGIN_LINES = (20,0,20,10)   # Margini segmentazione righe
MARGIN_LINE = (10,0,10,0)     # Margini GUI
BATCH_SIZE = 1                # Batch size per inference
LOCAL_MODEL = False           # Usa modello locale o HuggingFace
```

### 4.4 utils.py - Utility Generali

**Funzioni**:
- `save_file()`: Salva file con pickle
- `load_file()`: Carica file pickle
- `resource_path()`: Ottiene path assoluto (compatibile PyInstaller)
- `horizontal_projections()`: Proiezione orizzontale pixel
- `vertical_projections()`: Proiezione verticale pixel

### 4.5 toolbox/line_segmenter.py - Segmentazione Righe

**Funzioni Principali**:
- `compute_seg_mask()`: Genera maschera segmentazione con modello UNetMini
- `line_segm()`: Estrae righe usando proiezioni e peak finding
- Elaborazione immagini per segmentazione

**Flusso**:
1. Carica immagine documento
2. Passa modello UNetMini per generare maschera
3. Usa proiezioni orizzontali per trovare righe
4. Estrae bounding box righe

### 4.6 toolbox/word_segmenter.py - Segmentazione Parole

**Classe Principale**: `CustomThread` (thread con return value)

**Funzioni Principali**:
- `word_segm()`: Segmenta righe in parole usando easyOCR
- `word_segm_doc()`: Elabora intero documento
- `correct_segmentation_doc()`: Correzione post-processing segmentazione
- Gestione trascrizione easyOCR

**Usa**:
- easyOCR per rilevamento bounding box parole
- Thresholding e operazioni morfologiche

### 4.7 toolbox/trocr_manager.py - Manager TrOCR

**Funzioni Principali**:
- `predict_onedocument()`: Predizione completa documento
- `_get_similar_transcripts()`: Trova parole simili da dizionario

**Flusso Predizione**:
1. Carica processor TrOCR
2. Crea dataset da file .als
3. Predice trascrizioni
4. Integra con dizionario (opzionale)
5. Salva risultati in file .als

---

## <a name="flusso"></a>5. Flusso di Lavoro

### Workflow Tipico

```
┌─────────────────────────┐
│ Utente avvia GUI.py     │
└────────────┬────────────┘
             │
             ▼
    ┌────────────────────┐
    │ Carica documento   │
    │ Carica file .als   │
    └────────┬───────────┘
             │
             ▼
    ┌────────────────────────────┐
    │ Visualizza prima riga      │
    │ in interfaccia web         │
    └────────┬───────────────────┘
             │
             ▼
    ┌─────────────────────────────┐
    │ Utente corregge/conferma    │
    │ trascrizioni parole         │
    └────────┬────────────────────┘
             │
             ▼
    ┌──────────────────────────┐
    │ Naviga doc (riga/parola) │
    │ Salva trascrizioni       │
    └────────┬─────────────────┘
             │
             ▼
    ┌──────────────────┐
    │ Fine documento   │
    │ Esporta risultati│
    └──────────────────┘
```

### Workflow Predizione Automatica

```
predict_als.py (o trocr_manager.predict_onedocument)
      │
      ▼
Load file .als + immagine documento
      │
      ▼
TrocrPredictor.predict()
      │
      ├─▶ Carica immagini da file .als
      ├─▶ Passa a TrOCR
      ├─▶ Ottiene trascrizioni predette
      │
      ▼
Integrazione dizionario (opzionale)
      │
      ├─▶ Per ogni trascrizione
      ├─▶ Trova parole simili
      ├─▶ Aggiunge opzioni
      │
      ▼
Save file .als aggiornato
```

---

## <a name="installazione"></a>6. Installazione e Configurazione

### Requisiti di Sistema
- Sistema operativo: Windows, Linux, macOS
- Python 3.8+
- Anaconda o Miniconda
- GPU NVIDIA (opzionale, per accelerazione CUDA)
- RAM minimo: 4GB
- Storage: ~2GB (inclusi modelli)

### Installazione Passo per Passo

#### 1. Clonare/Scaricare il Progetto
```bash
cd /percorso/desiderato
# Scaricare il progetto
```

#### 2. Creare Ambiente Conda
```bash
conda env create -f environment.yml
conda activate librarius
```

#### 3. Preparare Struttura Dati
```bash
# Creare cartelle necessarie
mkdir -p data/doc_img
mkdir -p data/alignments
mkdir -p data/line_segmentation
mkdir -p data/logs
mkdir -p data/outs
```

#### 4. Aggiungere Dati
- Copiare immagini documenti in `data/doc_img/`
- Copiare file alignment (.als) in `data/alignments/`
- Copiare segmentazioni righe in `data/line_segmentation/`

(**Consigliato**)
In alternativa si possono caricare i documenti direttamente dall'interfaccia dell'applicazione. Al caricamento di un nuovo documento l'applicazione creera in automatico sia il file di segmentaione che il file di allineamento.

#### 5. Verificare Modelli
```bash
# I modelli dovrebbero trovarsi in:
models/line_segmenter/
models/trocr/
```

### Configurazione

#### configs.py
```python
PORT = 9565                    # Cambia se porta è occupata
MODE = "chrome"                # O "edge", "firefox", ecc.
BATCH_SIZE = 1                 # Aumenta se GPU disponibile
LOCAL_MODEL = False            # True se vuoi usare modello locale
```

#### environment.yml
Contiene tutti i pacchetti necessari:
- PyTorch + CUDA (opzionale)
- TorchVision
- OpenCV
- scikit-image
- easyocr
- transformers (HuggingFace)
- Eel (web framework)
- E molti altri...

---

## <a name="utilizzo"></a>7. Utilizzo dell'Applicazione

### Avvio Applicazione

```bash
# Attivare ambiente
conda activate librarius

# Avviare GUI
python GUI.py
```

L'applicazione:
1. Apre un browser (Chrome di default)
2. Si connette a `http://localhost:9565`
3. Mostra l'interfaccia web

### Interfaccia Web

**Sezioni Principali**:
- **Immagine Riga**: Visualizza riga testo attuale
- **Immagine Parola**: Zoom sulla parola attuale
- **Area Trascrizione**: Mostra trascrizioni doc
- **Input Trascrizione**: Modifica/conferma parola
- **Controlli**: Navigazione, salvataggio

**Comandi Tastiera** (da implementare nella GUI):
- **Freccia Su/Giù**: Naviga righe
- **Freccia Sinistra/Destra**: Naviga parole
- **Enter**: Conferma trascrizione
- **Escape**: Annulla modifica

### Workflow Utente

1. **Carica Documento**
   - Seleziona documento da dropdown
   - Sistema genera alignment e immagine

2. **Generare una trascrizione**
   - Avviare la trascrizione automatica con "Generate Transcription Options". Questa opaizone genera una lista di opzioni di trascrizione per ogni immagine di parola rilevata.
   - Cliccando su "Allpy Generated Transcription" il software genera una trascrizione per l'intero documento applicando la prima opzionde di trascrizione per ogni paorla.

2. **Naviga**
   - Usa pulsanti per parola successiva/precedente
   - Usa tastiera per parola. in questo caso usa la combinazione di tasti Alt+Freccia destra e sinistra per andare alla prossima/precedente parola
   - Si puo navigare a una spacifica parola con un doppio click sulla trascrizione

3. **Rivedi e Correggi**
   - Visualizza riga attuale
   - Per ogni parola:
     - Sistema mostra immagine e opzioni trascrizione
     - Scegli opzione corretta o digita manualmente
     - Conferma

4. **Cancella Parola**
   - Clccando sul tasto "Delete Work" o con la combinazione di tasti Alt+Del si puo eliminare il box di segmentazione della parola attuale.

5. **Correzione Segmentazione**
   - Cliccando il bottone "Correct Segmentation" il software analizzera la trascrizione fornita e si passera alla modalita di correzione della segmentazione.
   Il software analizzera la trascrizione e quindi:
      - fonderà in automatico i box corrispondenti a trascrizioni che termino/iniziano con il carattere '@' con il prossimo/precedente box.
      - creerà un nuovo box priama/dopo un boc che inizia/termina con il carattere '?'
      - mostrera all'utente una finesta di segmetnazione per tutte le parole che contengono il carattere '#'. L'utente porta decidere con un click del mouse dove voler effettuare il taglio

    (tutti i caratteri speciali possono essere modificati attraverso il file JSON like di configurazone 'config')


6. **Salva**
   - Salvataggio automatico
   - Export manuale disponibile

---

## <a name="api"></a>8. API ed Endpoint

### Endpoint Backend (Python/Eel)

Accessibili dal frontend JavaScript tramite `eel.functionName()`:

#### Caricamento Documenti
```python
@eel.expose
def load_document(doc=None)
# Carica documento specifico
# Parametri: doc (str) - nome file immagine
# Return: None (aggiorna UI tramite callback)
```

#### Navigazione
```python
@eel.expose
def get_next_row_image()
# Carica riga successiva
# Return: None (aggiorna UI)

@eel.expose
def get_prev_row_image()
# Carica riga precedente
# Return: None (aggiorna UI)
```

#### Gestione
```python
@eel.expose
def release_document()
# Scarica documento, pulisce risorse
# Return: None
```

#### Aggiornamento UI
```python
def _update_view(list_tr)
# Funzione interna
# Aggiorna:
#   - Area trascrizione (HTML)
#   - Input trascrizione
#   - Lista trascrizioni
#   - Immagini riga e parola
```

### Callback JavaScript (invocate da backend)

```javascript
eel.update_transcription_area(html)
// Aggiorna area trascrizione

eel.update_transcript_input(text)
// Aggiorna input parola corrente

eel.show_transcripts_list(list)
// Mostra lista opzioni trascrizione

eel.show_current_word_img(path)
// Mostra immagine parola corrente

eel.show_current_line_img(path)
// Mostra immagine riga corrente
```

---

## <a name="modelli"></a>9. Modelli di Machine Learning

### 9.1 Line Segmenter - UNetMini

**Architetto**: U-Net semplificato per segmentazione semantica

**Input**:
- Immagine documento (RGB)
- Dimensione: 800x800 pixel

**Output**:
- Maschera 3-canale (R, G, B)
- Ogni canale rappresenta classe: background, testo, righe

**Utilizzo**:
```python
from toolbox.line_segmenter import compute_seg_mask
mask = compute_seg_mask(checkpoint_path, image_path, out_dir)
```

**Processo**:
1. Carica checkpoint modello
2. Ridimensiona immagine a 800x800
3. Passa a modello
4. Estrae maschera per righe
5. Usa proiezioni per trovare boundary righe

### 9.2 TrOCR - Transformers Optical Character Recognition

**Modello**: `microsoft/trocr-base-handwritten` (da HuggingFace)

**Input**:
- Immagine parola (da segmentazione)
- Dimensione variabile

**Output**:
- Testo trascritto (stringa)
- Confidence score (opzionale)

**Utilizzo**:
```python
from toolbox.trocr_manager import predict_onedocument
als = predict_onedocument(als_path, img_path, words_dict="dicts/ita")
```

**Features**:
- Supporta lingue: Inglese, Italiano (tramite dizionari)
- Genera più opzioni di trascrizione
- Integrazione fuzzy matching con dizionario

**Configurazione**:
```python
LOCAL_MODEL = False  # Scarica da HuggingFace
LOCAL_MODEL = True   # Usa modello in models/trocr/
BATCH_SIZE = 1       # 1 per default
NUM_WORKERS = 0      # Aumenta su GPU potenti
```

### 9.3 easyOCR - Word Detection

**Utilizzo**: Segmentazione parole (bounding box)

**Input**:
- Immagine riga di testo

**Output**:
- Bounding box parole (x1, y1, x2, y2)
- Confidence score per rilevamento

**Linguaggi**: En, It (configurato in `word_segmenter.py`)

**Codice**:
```python
reader = easyocr.Reader(['en', 'it'])
results = reader.readtext(image)
# results: [(bbox, text, confidence), ...]
```

---

## <a name="formati"></a>10. Formati Dati

### 10.1 Formato File Alignment (.als)

**Descrizione**: File serializzato (pickle) che contiene struttura documento

**Struttura Dati**:
```python
{
    "doc_id": {                        # ID documento (es. "001_080_001")
        "line_id": [                   # ID riga (es. "0000")
            
            [                          # Elemento 0: Lista di bounding box delle parole nella riga
                (x1, y1, x2, y2),...   # Coordinate parola, ...
            ],
            
            [                          # Elemento 1: Lista di trascrizioni
                [                      # Parola 1
                    "trascrizione1",
                    "trascrizione2",
                    ...
                ],
                [...],                 # Parola 2
                ...
            ],
            [x1, y1, x2, y2]           # Elemento 2: Bounding box di riga
        ],
        ...
    },
    ...
}
```

**Esempio Concreto**:
```python
{
    "doc_001": {
        "001": [
            [(10, 20, 500, 50), (600, 20, 800, 60) ],   # Bounding box parole
            [
                ["Prima", "Parola"],
                ["Trascrizioni", "Seconda"],
            ],
            [0,0,1000,70]
        ],
        "002": [
            ...
       ]
    }
}
```

### 10.2 File Configurazione Dinamica (JavaScript)

#### configs.js
Generato automaticamente da `init_GUI()` in GUI.py

```javascript
const all_documents = [
    "001_080_001.jpg",
    "001_080_002.jpg",
    ...
];

const all_ls_models = [
    "models/line_segmenter/0195.pth",
    ...
];

const all_trocr_models = [
    "models/trocr/model1",
    ...
];
```

#### keyword_list.js
Generato da dizionario (.txt)

```javascript
var all_keywords = [
    "il",
    "gatto",
    "nero",
    ...
];
```

### 10.3 Formato Log Timing

**Localizzazione**: `data/logs/<ANNO>-<MESE>-<GIORNO>-<ORA>-<MINUTO>_words_timing.csv`

**Formato CSV**:
```
Doc_ID,line_ID,word_ID,transcript,mode,time_currentword_s,time_from_prevword_s
001,001,0,"il",manual,2.5,2.5
001,001,1,"gatto",auto,1.2,3.7
001,001,2,"nero",manual,1.8,5.5
...
```

**Campi**:
- `Doc_ID`: ID documento
- `line_ID`: ID riga
- `word_ID`: ID parola
- `transcript`: Trascrizione confermata
- `mode`: "manual" o "auto"
- `time_currentword_s`: Tempo per parola corrente (secondi)
- `time_from_prevword_s`: Tempo cumulative da inizio riga (secondi)

### 10.4 File Dizionario

**Localizzazione**: `dicts/eng`, `dicts/ita`, etc.

**Formato**: File di testo semplice
```
il
gatto
nero
...
```

Una parola per riga, minuscolo

**Utilizzo**:
```python
# In predict_als.py
python predict_als.py --als_path "data/alignments/001.als" \
                      --img_path "data/doc_img/001.jpg" \
                      --language "dicts/ita"
```

### 10.5 Struttura Immagini Elaborate

**Line Segmentation** (`data/line_segmentation/`):
- Cartella per ogni documento
- File `.txt` o binari con coordinate righe

**Line Segmentation Masks** (`data/line_segmentation_masks/`):
- Immagini PNG della maschera segmentazione
- Generato da `compute_seg_mask()`

**Output Transcriptions** (`data/outs/`):
- File `.dat` (pickle) con trascrizioni salvate
- Nome: `{doc_id}.dat`

---

## Conclusione

Librarius è un'applicazione complessa e ben strutturata che combina:
1. **Backend Python** solido per elaborazione immagini e ML
2. **Frontend Web** intuitivo per interazione utente
3. **Modelli State-of-the-Art** per riconoscimento testo
4. **Architettura modulare** per facilità manutenzione

Ogni componente ha responsabilità chiara, consentendo sviluppo e testing indipendenti.

Per contributi o modifiche, mantenere la separazione delle responsabilità tra moduli.
