#Correzione della Segmentazione

Il sistema permette di correggere errori di segmentazione (bounding boxes) interagendo direttamente con la **trascrizione del testo**. Inserendo caratteri speciali all'interno delle parole, l'algoritmo riconosce se deve unire, dividere o creare nuovi box.

> **Nota:** I simboli di default possono essere personalizzati nel file di configurazione JSON-like 'config'.

---

## Tipologie di Correzione

Il sistema gestisce i tre casi classici di errore nel riconoscimento del layout:

### 1. Missed (Creazione nuovi Box)

Si utilizza quando una parola nell'immagine non ha un bounding box corrispondente.

* **Simbolo di default:** `?`
* **Come procedere:** Inserisci la trascrizione mancante racchiusa tra i simboli `?` all'interno di un box esistente (prima o dopo la parola corrente).
* **Esempio:** Se il sistema ha mancato la parola "of", scrivi: 
```
The?of?
```
oppure
```
?of?The.
```
* **Risultato:** Verrà generato un nuovo box calcolato automaticamente nello spazio vuoto adiacente al box corrente (Dopo nel primo esempio, prima ne secondo esempio).


### 2. Under-segmentation (Divisione di un Box)

Si utilizza quando un singolo box contiene due o più parole distinte nell'immagine.

* **Simbolo di default:** `#` (vengono considerati anche lo spazio `     ` e il tab `\t` generati dalla trascrizione automatica).

* **Come procedere:** Inserisci il simbolo nel punto esatto della trascrizione dove le parole devono essere divise.
* **Esempio:** Trascrizione nel box: 
```
`engagement#consigned`.
```

* **Interfaccia GUI:** Una volta rilevato il simbolo, il sistema aprirà una finestra popup mostrando l'immagine del box. L'utente dovrà:
1. Cliccare sull'immagine nel punto esatto del taglio.
2. Confermare la scelta (tasto Invio o cliccando sul bottone OK).


* **Risultato:** Il box originale viene diviso in due parti basandosi sulla coordinata X cliccata.



### 3. Over-segmentation (Fusione di Box)

Si utilizza quando una singola parola è stata spezzata erroneamente in due o più bounding boxes.

* **Simbolo di default:** `@`
* **Come procedere:** Inserisci il simbolo all'inizio o alla fine della trascrizione per indicare la direzione della fusione.

```
`parola@`
```
Fonde il box corrente con quello **successivo**.

```
`@parola`
```
Fonde il box corrente con quello **precedente**.


* **Esempio:** Box 1: `inter@`, Box 2: `faccia`. Scrivendo `@` il sistema unirà le geometrie dei due box in un unico rettangolo che le contiene entrambe.

---



## Flusso di Lavoro e Salvataggio

Il metodo `correct_segmentation_doc` elabora i documenti seguendo una gerarchia precisa per evitare conflitti:

1. **Fase di Creazione:** Vengono prima gestiti tutti i nuovi box (`?`).
2. **Fase di Fusione:** Vengono uniti i box frammentati (`@`).
3. **Fase di Taglio:** Vengono processate le divisioni manuali (`#`) tramite l'interfaccia grafica.

### Sicurezza dei dati

* **Salvataggio Incrementale:** Il sistema salva lo stato dei file `.als` e `.dat` dopo l'elaborazione di **ogni singola riga**. In caso di crash o chiusura improvvisa, il lavoro precedente è al sicuro.
* **Annullamento:** È possibile interrompere l'intero processo premendo il tasto "ANNULLA" nella GUI. Il sistema catturerà l'eccezione `SegmentationCancelled`, interromperà i cicli e preserverà l'integrità dei file.

---

### Configurazione Rapida (JSON)

Assicurati che i simboli nel tuo file `config` corrispondano a quelli desiderati:

```json
{
    ...

  "split_ch": "#",
  "fuse_ch": "@",
  "create_ch": "?"
}

```
