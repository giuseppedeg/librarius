# Guida Tecnica Avanzata - Librarius

## Indice
1. [Dettagli Implementazione](#implementazione)
2. [Modelli Machine Learning](#modelli-ml)
3. [Pipeline Elaborazione Immagine](#pipeline)
4. [Gestione Stato Applicazione](#stato)
5. [Comunicazione Frontend-Backend](#comunicazione)
6. [Estensioni e Personalizzazioni](#estensioni)
7. [Performance e Ottimizzazioni](#performance)
8. [Troubleshooting](#troubleshooting)

---

## <a name="implementazione"></a>1. Dettagli Implementazione

### 1.1 Flusso di Inizializzazione

```
Avvio GUI.py
    ↓
Reindirizzamento stdout/stderr (per logging)
    ↓
Caricamento moduli (configs, eel, corrector_business, utils)
    ↓
Creazione Handler principale
    ├─ base_folder = "data"
    └─ Inizializzazione logger CSV timing
    ↓
Verifica porta disponibile (socket)
    ↓
init_GUI()
    ├─ Scansione cartella doc_img
    ├─ Scansione cartella modelli
    ├─ Generazione configs.js
    ├─ Generazione keyword_list.js
    └─ Chiusura splash screen
    ↓
Avvio server Eel
    ├─ Binding @eel.expose functions
    ├─ Caricamento www/index.html
    └─ Apri browser su localhost:PORT
    ↓
Attesa eventi utente
```

### 1.2 Struttura File Alignment (.als)

**Serializzazione**: Pickle (Python binary format)

**Struttura Dati**:
```python
{
    "doc_id": {                              # Es: "001_080_001"
        "line_name": [                       # Es: "line_001"
            [                                # Elemento 0: Lista di Bbox riga
                (x1, y1, x2, y2), ...        # Coordinate assolute immagine
            ],
            [                                # Elemento 1: Trascrizioni parole
                ["trascrizione1", ...],      # Parola 1 - liste opzioni
                ["trascrizione2", ...],      # Parola 2
                ...
            ],
            [x, y1, x2, y2]                  # Bounding Box riga
        ]
    }
}
```

**Esempio Concreto**:
```python
{
    "001": {
        "001": [
            [(10, 20, 500, 50), (550, 20, 800, 55)],          # Lista Bounding box delle parole
            [
                ["il", "Il"],              # Opzioni parola 1
                ["gatto", "gato"],         # Opzioni parola 2
            ],
            [0, 0, 1000, 80]               # Bounding box riga
        ]
    }
}
```

### 1.3 Struttura File Transcription (.dat)

**Serializzazione**: Pickle

**Struttura Dati** (contiene trascrizioni confermata dall'utente):
```python
{
    "doc_id": {                    # Es: "001"
        "line_id": {               # Es: "001" (0-indexed)
            0: "il",               # Word 0 → trascrizione confermata
            1: "gatto#nero",       # Word 1 → con SPLIT_CH (#) per segmentazione
            2: "corre",            # Word 2
            ...
        }
    }
}
```

**Nota**: I valori possono contenere caratteri speciali:
- `#` (SPLIT_CH): Divide parola in sotto-parole
- `@` (FUSE_CH): Fonde due parole
- `?` (CREATE_CH): Crea parola nuova

questi valori possono essere personalizzati modificando il file di configurazione JSON-line 'config':

```
{
    ...

    "split_ch": "#",
    "fuse_ch": "@",
    "create_ch": "?"
}
```


### 1.4 Bounding Box: Coordinate e Convenzioni

**Sistema Coordinate**: Pixel assoluti dell'immagine originale

**Format Bounding Box**: `(x1, y1, x2, y2)`
- `x1, y1`: Top-left corner
- `x2, y2`: Bottom-right corner
- Unità: Pixel
- Origine: Top-left immagine

**Conversione Box Riga**:
```python
# Da file segmentazione
id, x, y, l, h = (int, int, int, int, int)  # l=larghezza, h=altezza

# A bbox standard
bbox = (x, y, x+l, y+h)
```

---

## <a name="modelli-ml"></a>2. Modelli Machine Learning

### 2.1 Line Segmenter - UNetMini

**Architettura**: U-Net semplificato
- Input: 800x800 RGB
- Output: 800x800 3-canale (R, G, B)
- Encoder-Decoder con skip connections

**Utilizzo**:
```python
from toolbox.line_segmenter import compute_seg_mask

# Genera maschera
mask = compute_seg_mask(
    checkpoint="models/line_segmenter/0195.pth",
    image_path="data/doc_img/001.jpg",
    out_imgs_dir="data/line_segmentation_masks"
)

# Ritorna: PIL Image con maschera
```

**Output**: 3 canali
- **Red (R)**: Background
- **Green (G)**: Testo (foreground)
- **Blue (B)**: Linee separa-rige

**Processamento Output**:
1. Carga PIL Image da disco
2. Estrae array NumPy
3. Analizza canali separatamente
4. Usa proiezioni orizzontali per trovare righe
5. Peak detection per boundary

**Device**: Auto GPU se disponibile CUDA, altrimenti CPU

### 2.2 TrOCR - Microsoft Transformer OCR

**Modello Base**: `microsoft/trocr-base-handwritten`
- Scaricato da HuggingFace model hub
- Transformer-based (Encoder-Decoder)
- Input: Immagine parola variabile
- Output: Testo trascritto + confidence score

**Configurazione**:
```python
# In trocr_manager.py
from trocr.main import TrocrPredictor

# Opzione 1: HuggingFace online (default)
predictor = TrocrPredictor(local_model=False)

# Opzione 2: Modello locale
predictor = TrocrPredictor(local_model="models/trocr/model_checkpoint")
```

**Processamento**:
1. Load processor TrOCR
2. Per ogni parola dal file .als:
   - Estrai immagine from document
   - Normalizza dimensioni
   - Passa a TrOCR
   - Ottiene testo predetto
3. Post-processing:
   - Integra fuzzy matching dizionario
   - Aggiunge opzioni trascrizione

**Fuzzy Matching**:
```python
from rapidfuzz import fuzz, process

# Per ogni trascrizione predetta
generated = "il"

# Trova simili nel dizionario
similar = process.extract(
    generated,
    dic_words,
    scorer=fuzz.token_sort_ratio,
    limit=3,        # Top 3 simili
    score_cutoff=0  # Threshold minimo
)

# Risultato: [("il", 100, index0), ("Il", 90, index1), ...]
```

### 2.3 easyOCR - Word Detection

**Utilizzo in word_segmenter.py**:
```python
import easyocr

# Inizializza reader
reader = easyocr.Reader(['en', 'it'])

# Rileva parole
results = reader.readtext(image_riga)

# Formato output
# [
#   (bbox, text, confidence),
#   ([(x1,y1), (x2,y2), (x3,y3), (x4,y4)], "testo", 0.95),
#   ...
# ]
```

**Bounding Box**: Poligono 4-punti (non rettangolo)
- Necessario convertire in bbox rettangolo standard per file .als

**Confidence Threshold**: TEXT_THRESHOLD = 0.7
- Ignora rilevamenti con confidence < 0.7

---

## <a name="pipeline"></a>3. Pipeline Elaborazione Immagine

### 3.1 Caricamento Documento (load_document)

```
Utente seleziona documento
    ↓
GUI.load_document(doc_name)
    ├─ handeler.reinit(doc_name)
    │  ├─ Carica immagine documento
    │  ├─ Carica file alignment (.als)
    │  └─ Carica transcriptions (.dat) se exist
    │
    ├─ handeler.load_line_segmentations_info()
    │  ├─ Apre immagine documento
    │  └─ Carica coordinate righe da file testo
    │
    ├─ handeler.current_word()
    │  └─ Inizializza prima parola, avvia timer
    │
    ├─ handeler.get_current_line_word_img()
    │  ├─ Estrae immagine riga
    │  ├─ Estrae immagine parola
    │  ├─ Salva www/images/current_row.png
    │  └─ Salva www/images/current_word.png
    │
    └─ _update_view()
       ├─ Aggiorna area trascrizione
       ├─ Aggiorna input parola
       ├─ Aggiorna lista opzioni
       └─ Mostra immagini
```

### 3.2 Upload e Processamento Nuova Immagine (add_new_image)

```
Utente seleziona file immagine
    ↓
GUI.uploadImage(ls_model)
    ├─ File dialog select
    └─ handeler.add_new_image(path, ls_model)
       │
       ├─ Step 1: Copia immagine
       │  ├─ Copia in data/doc_img/
       │  ├─ Converte in JPG se necessario
       │  └─ Gestisce conflitti nome (somma _2, _3)
       │
       ├─ Step 2: Line Segmentation
       │  ├─ compute_seg_mask()
       │  │  ├─ Load UNetMini checkpoint
       │  │  ├─ Infer maschera
       │  │  └─ Salva in data/line_segmentation_masks/
       │  │
       │  └─ line_segm()
       │     ├─ Estrae righe dalla maschera
       │     └─ Salva coordinate in data/line_segmentation/
       │
       ├─ Step 3: Word Segmentation
       │  └─ word_segm_doc()
       │     ├─ Carica righe segmentate
       │     ├─ Per ogni riga:
       │     │  ├─ easyOCR.readtext()
       │     │  ├─ Estrae bbox parole
       │     │  └─ Crea entry in alignment
       │     └─ Salva file .als in data/alignments/
       │
       ├─ Step 4: Cleanup
       │  └─ Rimuovi masks temporanee
       │
       └─ Return path immagine
```

### 3.3 Transcription automatica (transcribe)

```
Utente clicca "Transcribe"
    ↓
GUI.transcribe(htr_model, num_options, language)
    │
    ├─ Launch thread separato
    │  │
    │  └─ running_process()
    │     │
    │     ├─ handeler.transcribe()
    │     │  └─ trocr_manager.predict_onedocument()
    │     │     │
    │     │     ├─ Load TrocrPredictor(htr_model)
    │     │     │
    │     │     ├─ Load file .als
    │     │     │
    │     │     ├─ Per ogni parola:
    │     │     │  ├─ Estrai immagine parola da documento
    │     │     │  ├─ TrOCR.infer(immagine)
    │     │     │  ├─ generated_text = output
    │     │     │  │
    │     │     │  ├─ Se language (dizionario):
    │     │     │  │  ├─ _get_similar_transcripts(generated_text, dic)
    │     │     │  │  └─ all_options = [generated] + [simili]
    │     │     │  │
    │     │     │  └─ Aggiorna file .als con opzioni
    │     │     │
    │     │     └─ Save file .als aggiornato
    │     │
    │     ├─ handeler.reinit_als()  # Ricarica file .als
    │     │
    │     ├─ _update_view()  # Aggiorna UI
    │     │
    │     └─ eel.hide_modal_create_trans()
    │
    └─ Return (thread continua background)
```

---

## <a name="stato"></a>4. Gestione Stato Applicazione

### 4.1 Variabili di Stato Principali

**Nella classe Handeler**:

```python
# Documento e Immagine
document_img_name: str           # Es: "001_080_001.jpg"
als_file_path: str              # Path file alignment
alignments_file: dict           # Struttura dati documento in memoria
current_doc_img: PIL.Image      # Immagine documento (full resolution)

# Posizioni Correnti
current_doc_id: int             # Indice documento (0-indexed)
current_row_id: int             # Indice riga (0-indexed)
current_word_id: int            # Indice parola (0-indexed)

# Strutture Riga Corrente
all_boxes: list[tuple]          # Bounding box parole [(x1,y1,x2,y2), ...]
all_transcripts_list: list      # Opzioni trascrizioni [[...], [...], ...]

# Immagini Cache
current_row_img: PIL.Image      # Immagine riga corrente
current_word_img: PIL.Image     # Immagine parola corrente

# Trascrizioni Salvate
current_transcription: dict     # {doc: {line: {word_id: text, ...}, ...}, ...}
out_transcription_file: str     # Path file .dat trascrizioni

# Timer Tracking
_currentword_timer_start: float
_frompreviousword_timer_start: float
_currentword_timer: float
_frompreviousword_timer: float

# Logging
_current_wordstiming_log: str   # Path file CSV timing
```

### 4.2 Transizioni di Stato

**Navigazione Documento**:
```
next_word():
    current_word_id += 1
    if current_word_id >= len(all_boxes):
        current_word_id = 0
        current_row_id += 1
        if current_row_id >= len(rows):
            current_row_id = 0
            current_doc_id += 1

prev_word():
    current_word_id -= 1
    if current_word_id < 0:
        current_row_id -= 1
        if current_row_id < 0:
            current_doc_id -= 1
```

**Cambio Documento**:
```
load_document(doc):
    reinit(doc)                           # Carica .als
    load_line_segmentations_info()        # Carica righe
    current_word()                        # Init parola
```

### 4.3 Persistenza Stato

**Salvataggio Automatico**:
```
Ogni volta che set_current_word_transcription() viene chiamato:
    1. Salva in memoria: current_transcription
    2. Salva su disco: out_transcription_file (pickle)
    3. Registra nel log CSV
```

**Caricamento All'avvio**:
```
load_document():
    1. Load document image
    2. Load alignment file (.als)
    3. Load transcription file (.dat) se esiste
    4. Merge di alignment e transcription
```

---

## <a name="comunicazione"></a>5. Comunicazione Frontend-Backend

### 5.1 Architettura Eel

**Eel**: Framework per comunicazione bidirrezionale tra Python e JavaScript

**Binding**: @eel.expose decorator espone funzione Python a JavaScript

```python
@eel.expose
def funzione_python(param):
    """Richiamabile da JavaScript"""
    return risultato

# JavaScript
var result = await eel.funzione_python(param)();
```

### 5.2 API Esposte (Backend → Frontend)

**Funzioni esposte dal backend** (chiamabili da JS):

```python
@eel.expose
def load_document(doc=None)              # Carica documento

@eel.expose
def next_word()                          # Naviga parola successiva

@eel.expose
def prev_word()                          # Naviga parola precedente

@eel.expose
def to_word(word_id, line_id)           # Vai a parola specifica

@eel.expose
def set_current_word_transcription(text, mode)  # Salva trascrizione

@eel.expose
def delete_current_word()                # Cancella parola

@eel.expose
def correct_segmentation()               # Ricorreggi segmentazione

@eel.expose
def clear_transcripts()                  # Cancella tutte trascrizioni

@eel.expose
def apply_transcription()                # Applica trascrizioni

@eel.expose
def transcribe(htr_model, num_options, language)  # Auto-trascrivi

@eel.expose
def uploadImage(ls_model, wildcard)     # Upload nuova immagine

@eel.expose
def deleteImage(id_img)                  # Cancella documento

@eel.expose
def release_document()                   # Scarica documento

@eel.expose
def start_currentword_timer()            # Avvia timer parola

@eel.expose
def stop_currentword_timer()             # Ferma timer parola

@eel.expose
def start_previousword_timer()           # Avvia timer da prev

@eel.expose
def stop_previousword_timer()            # Ferma timer da prev

@eel.expose
def select_transcript(text)              # Seleziona trascrizione (lista)
```

### 5.3 Callback Funzioni (Frontend → Backend)

**Funzioni JavaScript richiamate da Python** (tramite eel):

```javascript
// In www/js/main.js o simile

eel.update_transcription_area(html)      // Aggiorna area trascrizioni

eel.update_transcript_input(text)        // Aggiorna input parola

eel.show_transcripts_list(list)          // Mostra opzioni trascrizione

eel.show_current_word_img(path)          // Mostra immagine parola

eel.show_current_line_img(path)          // Mostra immagine riga

eel.hide_modal_load_document()           // Chiudi dialog upload

eel.hide_modal_create_trans()            // Chiudi dialog progresso

// Funzioni di callback implementate nel frontend
```

### 5.4 Sequenze di Comunicazione

**Sequenza Caricare Documento**:
```
JavaScript: eel.load_document(doc_name)()
    ↓
Python: load_document(doc_name)
    ├─ handeler.reinit()
    ├─ handeler.load_line_segmentations_info()
    ├─ handeler.current_word()
    ├─ handeler.get_current_line_word_img()
    └─ _update_view(list_tr)
       ├─ eel.update_transcription_area(html)
       ├─ eel.update_transcript_input(text)
       ├─ eel.show_transcripts_list(list_tr)
       ├─ eel.show_current_word_img(path)
       └─ eel.show_current_line_img(path)
    ↓
JavaScript: Callback functions update UI
```

**Sequenza Salvare Trascrizione**:
```
JavaScript: eel.set_current_word_transcription(text, mode)()
    ↓
Python: set_current_word_transcription(text, mode)
    ├─ Normalizza testo
    ├─ stop_currentword_timer()
    ├─ handeler.set_curent_transcript(text)
    ├─ handeler.log_lastword(text, mode)
    ├─ start_previousword_timer()
    └─ next_word()
       ├─ handeler.next_word()
       ├─ handeler.get_current_line_word_img()
       └─ _update_view(list_tr)
          └─ [callbacks come sopra]
    ↓
JavaScript: Callback updates UI e avanza
```

---

## <a name="estensioni"></a>6. Estensioni e Personalizzazioni

### 6.1 Aggiungere Nuovo Modello HTR

**Passo 1**: Scaricare modello HuggingFace
```bash
git clone https://huggingface.co/user/model_name models/trocr/model_name
```

**Passo 2**: Modificare trocr_manager.py
```python
# Aggiungere supporto per nuovo modello
if htr_model == "models/trocr/model_name":
    from transformers import VisionEncoderDecoderModel
    model = VisionEncoderDecoderModel.from_pretrained(htr_model)
```

**Passo 3**: Aggiornare GUI
- Il nuovo modello appare automaticamente in dropdown
- Generato da init_GUI() scandendo cartella models/trocr/

### 6.2 Aggiungere Nuovo Dizionario Lingua

**Passo 1**: Creare file dizionario
```bash
# Formato: una parola per riga, minuscolo
echo "parola1" >> dicts/lingua_nuova
echo "parola2" >> dicts/lingua_nuova
```

**Passo 2**: Usare nella trascrizione
```bash
python predict_als.py --als_path data/alignments/001.als \
                      --img_path data/doc_img/001.jpg \
                      --language dicts/lingua_nuova
```

### 6.3 Personalizzare Caratteri Speciali

Modificare `configs.py`:
```python
SPLIT_CH = "#"      # Carattere split parola (default #)
FUSE_CH = "@"       # Carattere fuse parola (default @)
CREATE_CH = "?"     # Carattere crea parola (default ?)
```

### 6.4 Modificare Margini Visualizzazione

Modificare `configs.py`:
```python
MARGIN_LINES = (20, 0, 20, 10)  # (left, top, right, bottom) - righe
MARGIN_LINE = (10, 0, 10, 0)    # (left, top, right, bottom) - riga
MARGIN_WORD = (10, 0, 10, 0)    # (left, top, right, bottom) - parola
```

Oppure custom config file:
```json
{
    "margin_lines": [20, 0, 20, 10],
    "margin_line": [10, 0, 10, 0],
    "margin_word": [10, 0, 10, 0]
}
```

---

## <a name="performance"></a>7. Performance e Ottimizzazioni

### 7.1 Bottleneck Principali

**Line Segmentation**:
- Modello UNetMini: ~1-2 secondi per immagine (GPU)
- Proiezioni orizzontali: ~0.1 secondi

**Word Segmentation**:
- easyOCR: ~1-3 secondi per riga (primo caricamento GPU)
- Processing: ~0.1 secondi per riga

**HTR Prediction**:
- TrOCR: ~200-500ms per parola (GPU)
- Fuzzy matching: ~10-50ms per parola (dizionario)

**Upload Immagine**: ~5-15 secondi (linea+parola seg)

### 7.2 Ottimizzazioni Possibili

**GPU Memory**:
```python
# In toolbox/line_segmenter.py
import torch
torch.cuda.empty_cache()  # Libera memoria GPU
```

**Batch Processing**:
```python
# Aumentare BATCH_SIZE in configs.py
BATCH_SIZE = 4  # Default 1, max dipende da GPU
```

**Threading**:
```python
# transcribe() è già asincrono (threading)
# Per thread pool di parole: usare concurrent.futures
```

**Cache Immagini**:
```python
# Attualmente caricamento immagini in memoria
# Documento intero caricato una volta
# Righe e parole estratte al bisogno
```

## <a name="profiling"></a>8. Profiling

**Profile time trascrizione**:
```python
# Automatico tramite log CSV timing
# data/logs/<DATE>_words_timing.csv
```

**Profile memoria**:
```python
import tracemalloc
tracemalloc.start()
# ... codice ...
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')
for stat in top_stats[:10]:
    print(stat)
```

---

## <a name="troubleshooting"></a>9. Troubleshooting

### Problema: Porta già in uso
**Soluzione**:
```python
# Opzione 1: Cambia porta in configs.py
PORT = 9566

# Opzione 2: Usa file config JSON
# Crea file "configs":
# {"port": 9566}
```

### Problema: Modelli non trovati
**Soluzione**:
```bash
# Verifica cartelle
ls -la models/line_segmenter/
ls -la models/trocr/

# Se vuoti, scarica modelli HuggingFace
```

### Problema: GPU non detected
**Soluzione**:
```python
# Verifica torch CUDA
import torch
print(torch.cuda.is_available())  # Deve essere True

# Installa GPU CUDA support
# conda install pytorch::pytorch pytorch::torchvision pytorch::torchaudio cudatoolkit=11.8 -c pytorch -c nvidia
```

### Problema: OutOfMemory durante trascrizione
**Soluzione**:
```python
# Riduci batch size in configs.py
BATCH_SIZE = 1

# Oppure processa documento in parti
```

### Problema: Dizionario non caricato
**Soluzione**:
```bash
# Verifica file dizionario esista
ls -la dicts/ita

# Se manca, crea file
echo "parola1" > dicts/ita
```

### Problema: File .als corrotto
**Soluzione**:
```python
# Usa als_read.py per editare/rigenerare
python als_read.py

# O rigenera da zero tramite GUI upload
```

### Problema: Unicode/Encoding
**Soluzione**:
```python
# Assicura encoding UTF-8
with open(file, "r", encoding='utf-8') as f:
    data = f.read()
```

---

## Conclusione

Questa guida tecnica fornisce comprensione approfondita dell'architettura Librarius.
Per domande specifiche, consultare docstring nel codice o aprire issue nel repository.
