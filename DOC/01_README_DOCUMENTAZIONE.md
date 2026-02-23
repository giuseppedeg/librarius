# Librarius - Documentazione Progetto (Summary)
## 📋 Documentazione
Sono state create **4 guide complete** in italiano per il progetto Librarius:

### 1. **DOCUMENTAZIONE.md** - Documentazione Principale
   - Panoramica del progetto
   - Architettura del sistema
   - Struttura delle cartelle
   - Moduli principali con responsabilità
   - Flussi di lavoro (utente e automatico)
   - Installazione e configurazione
   - Utilizzo dell'applicazione
   - API ed endpoint
   - Modelli di Machine Learning
   - Formati dati (.als, .dat, CSV logging)

### 2. **GUIDA_TECNICA.md** - Guida Tecnica Avanzata
   - Dettagli implementazione
   - Strutture dati complete (alignments, transcriptions)
   - Bounding box e coordinate
   - Specifiche modelli ML:
     - UNetMini (Line Segmentation)
     - TrOCR (Handwritten Text Recognition)
     - easyOCR (Word Detection)
   - Pipeline elaborazione immagine
   - Gestione stato applicazione
   - Comunicazione Frontend-Backend (Eel)
   - Sequenze di comunicazione
   - Estensioni e personalizzazioni
   - Performance e ottimizzazioni
   - Troubleshooting e soluzioni

### 3. **GUIDA_COMMENTI.md** - Guida ai Commenti nel Codice
   - Struttura commenti consigliata
   - Docstring per moduli, classi, funzioni
   - Commenti file specifici (GUI.py, corrector_business.py, toolbox)
   - Convenzioni di commento
   - Priorità aggiunta commenti

### 4. **GUIDA_TESTING.md** - Testing e Debug
   - Setup ambiente test
   - Test unitari (utils, configs, handler)
   - Test integrazione
   - Debug locale con breakpoints
   - Logging e monitoring
   - Testing modelli ML
   - Checklist pre-release
   ---


## 🎯 Struttura Progetto
```
Librarius/
├── 📁 DOC/                       ← Documentazione
│   ├── 📄 00_DOCUMENTAZIONE_SUMMARY.txt  ← Overview doc
│   ├── 📄 01_README_DOCUMENTAZIONE.md    ← Documentazione Generica
│   ├── 📄 02_DOCUMENTAZIONE.md           ← Documentazione Generica
│   └── 📄 03_GUIDA_TECNICA.md            ← Dettagli tecnici
│
├── 📄 readme.md                  ← Veloce start
│
├── 🐍 GUI.py                     ← Entry point app (interfaccia web)
├── 🐍 corrector_business.py      ← Handler logica core
├── 🐍 configs.py                 ← Configurazioni globali
├── 🐍 utils.py                   ← Utility comuni
├── 🐍 image_utils.py             ← Utility immagini
├── 🐍 als_read.py                ← CLI editor .als files
├── 🐍 predict_als.py             ← Predizione standalone
│
├── 📁 toolbox/                   ← Moduli core
│   ├── line_segmenter.py         ← Segmentazione righe
│   ├── line_segmenter_model.py   ← Modello UNetMini
│   ├── word_segmenter.py         ← Segmentazione parole
│   └── trocr_manager.py          ← Manager TrOCR
│
├── 📁 trocr/                     ← TrOCR personalizzato
├── 📁 www/                       ← Frontend web (HTML/JS/CSS)
├── 📁 data/                      ← Dati applicazione
│   ├── doc_img/                  ← Immagini input
│   ├── alignments/               ← File .als
│   ├── line_segmentation/        ← Coordinate righe
│   ├── logs/                     ← Log timing CSV
│   └── outs/                     ← Trascrizioni output
├── 📁 models/                    ← Modelli pre-addestrati
│   ├── line_segmenter/           ← Checkpoint UNet
│   └── trocr/                    ← Modelli TrOCR
├── 📁 dicts/                     ← Dizionari linguistici
│   ├── eng                       ← Inglese
│   └── ita                       ← Italiano
└── environment.yml               ← Dipendenze Conda
```
---

## 🚀 Come Iniziare
### 1. **Installazione Ambiente**
```bash
conda env create -f environment.yml
conda activate librarius
```

### 2. **Preparazione Dati**
```bash
mkdir -p data/{doc_img,alignments,line_segmentation,logs,outs}
# Aggiungere immagini in data/doc_img/
```

### 3. **Avvio Applicazione**
```bash
python GUI.py
# Apre http://localhost:9565 nel browser
```

### 4. **Workflow Base**
1. Carica documento da dropdown
2. Per ogni parola:
   - Visualizza immagine
   - Scegli/digita trascrizione
   - Conferma (Enter o OK)
   3. Salva trascrizioni
---

## 🔧 Configurazione
### File `configs.py`
```python
PORT = 9565                    # Porta web server
BATCH_SIZE = 1                 # Batch per GPU
LOCAL_MODEL = False            # Usa HuggingFace
MARGIN_LINES = (20,0,20,10)    # Margini segmentazione
```

### File `configs` (JSON, opzionale)
```json
{
    "port": 9565,
    "margin_line": [10, 0, 10, 0],
    "margin_word": [10, 0, 10, 0],
    "split_ch": "#",
    "fuse_ch": "@",
    "create_ch": "?",
    "mode": "chrome"
    }
```
---

## 📊 Flussi Principali
### Caricamento Documento
```
GUI.load_document()
  ├─ Handeler.reinit()
  ├─ Handeler.load_line_segmentations_info()
  ├─ Handeler.current_word()
  ├─ Handeler.get_current_line_word_img()
  └─ _update_view() → Aggiorna UI
  ```
### Trascrizione Automatica
```
GUI.transcribe(htr_model, num_options, language)
  ├─ Thread: running_process()
  │   ├─ Handeler.transcribe()
  │   │   └─ trocr_manager.predict_onedocument()
  │   ├─ Handeler.reinit_als()
  │   └─ _update_view()
  └─ hide_modal()
  ```
### Upload Nuova Immagine
```
GUI.uploadImage()
  └─ Handeler.add_new_image()
      ├─ Copia immagine in data/doc_img/
      ├─ compute_seg_mask() → UNetMini
      ├─ line_segm() → Estrai righe
      └─ word_segm_doc() → easyOCR → .als
```
---

## 🔌 API Backend (Esposte a JavaScript)
**Gestione Documento**
- `load_document(doc)` - Carica documento
- `release_document()` - Scarica documento
**Navigazione**
- `next_word()` - Parola successiva
- `prev_word()` - Parola precedente
- `to_word(word_id, line_id)` - Vai a parola specifica
**Trascrizione**
- `set_current_word_transcription(text, mode)` - Salva trascrizione
- `transcribe(htr_model, num_options, language)` - Auto-trascrivi
- `delete_current_word()` - Cancella parola
- `clear_transcripts()` - Cancella tutte
- `apply_transcription()` - Applica trascrizioni
**Segmentazione**
- `correct_segmentation()` - Ricorreggi parole
**Media**
- `uploadImage(ls_model)` - Nuovo documento
- `deleteImage(id_img)` - Rimuovi documento
**Timer**
- `start_currentword_timer()` / `stop_currentword_timer()`
- `start_previousword_timer()` / `stop_previousword_timer()`
---

## 🤖 Modelli Machine Learning
### Line Segmenter
- **Modello**: UNetMini (custom)
- **Input**: Immagine 800x800 RGB
- **Output**: Maschera 3-canale
- **Peso**: ~50-100MB
- **Tempo**: ~1-2s per immagine (GPU)
### TrOCR
- **Modello**: `microsoft/trocr-base-handwritten`
- **Input**: Immagine parola variabile
- **Output**: Testo + confidence
- **Peso**: ~500MB
- **Tempo**: ~200-500ms per parola (GPU)
### easyOCR
- **Utilizzo**: Rilevamento parole (bbox)
- **Lingue**: Inglese, Italiano
- **Tempo**: ~1-3s per riga (primo caricamento)
---
## 📁 Formati Dati
### File .als (Alignment)
```python
# Pickle binary format
{
    "doc_id": {
        "line_id": [
            [(x1,y1,x2,y2)],  # Bbox riga
            [[trascrizioni_parola1], [trascrizioni_parola2], ...]
        ]
    }
}
```
### File .dat (Transcriptions)
```python
{
    "doc_id": {
        "line_id": {
            0: "trascrizione_confermata_parola0",
            1: "trascrizione_confermata_parola1",
            ...
        }
    }
}
```
### Log CSV Timing
```csv
Doc_ID,line_ID,word_ID,transcript,mode,time_currentword_s,time_from_prevword_s
001,001,0,"il",manual,2.5,2.5
001,001,1,"gatto",auto,1.2,3.7
```
---

## 🐛 Troubleshooting Rapido
| Problema | Soluzione |
|----------|----------|
| **Porta già in uso** | Cambia PORT in configs.py |
| **GPU non rilevata** | Verifica `torch.cuda.is_available()` |
| **Modelli non trovati** | Controlla models/ directory |
| **OutOfMemory** | Riduci BATCH_SIZE |
| **File .als corrotto** | Ricrea con upload immagine |
| **Unicode encoding** | Usa `encoding='utf-8'` sempre |
---


### Aggiungere Commenti al Codice
Segui [GUIDA_COMMENTI.md](GUIDA_COMMENTI.md):
- Docstring moduli
- Docstring classi e funzioni
- Commenti sezioni importanti
- Priorità: Alta per funzioni esposte, Media per flussi complessi

### Testing
Vedi [GUIDA_TESTING.md](GUIDA_TESTING.md):
```bash
python -m pytest test_*.py -v
```
---

---
**Documentazione creata: Febbraio 2026**
**Versione: 1.0**
**Status: Completa e pronta all'uso**
"