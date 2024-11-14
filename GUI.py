import os
import sys
import io
logfile = io.StringIO()
sys.stdout = logfile
sys.stderr = logfile

import eel
from corrector_business import Handeler
import configs
from time import sleep, time
from utils import resource_path

BASE_PATH = os.path.split(sys.argv[0])[0]
#BASE_PATH = os.getcwd()


handeler = Handeler(os.path.join(BASE_PATH,"data"))

DOCUMENT_JS_FILEPATH = resource_path(os.path.join("www","data","documents.js"))
DOCUMENT_IMAGE_FOLDER = os.path.join(BASE_PATH,"data","doc_img")
LOG_FOLDER = os.path.join(BASE_PATH,"data","logs")

start = time()

def init_GUI():
    with open(DOCUMENT_JS_FILEPATH, "w") as document_js_file:
        document_js_file.write("const all_documents = [")
        for page_img in os.listdir(DOCUMENT_IMAGE_FOLDER):
            document_js_file.write(f'"{page_img}",')
        document_js_file.write("]")
        

@eel.expose
def get_next_row_image():
    print("next_row")

@eel.expose
def get_prev_row_image():
    print("prev_row")


def _update_view(list_tr):
    transcription = handeler.get_currentpage_transcription()
    eel.update_transcription_area(transcription)
    eel.show_transcripts_list(list_tr)
    eel.show_current_word_img(configs.WORD_IMAGE_INVIEW.replace("www", "."))
    eel.show_current_line_img(configs.ROW_IMAGE_INVIEW.replace("www", "."))


@eel.expose
def load_document(doc):
    handeler.reinit(doc)

    handeler.current_word()
    handeler._load_line_segmentations_info()
    list_tr = handeler.get_transcript_list()
    handeler.get_current_line_word_img()

    _update_view(list_tr)   

    
@eel.expose
def next_word():
    handeler.next_word()
    list_tr = handeler.get_transcript_list()
    handeler.get_current_line_word_img()

    sleep(0.05)  # otherwise problem in list on page
    _update_view(list_tr)


@eel.expose
def prev_word():
    handeler.prev_word()
    list_tr = handeler.get_transcript_list()
    handeler.get_current_line_word_img()

    _update_view(list_tr)


@eel.expose
def select_transcript(text):
    print(text)

@eel.expose
def set_current_word_transcription(text, mode="none"):
    """
    mode defines the modality of input:
        OK -> ok button
        LIST_ID -> click on list item. ID is the position of the item in the list
                   if indefined, the list is the autocomplation
        ENTER -> click enter key
    """
    # SALVA TRASCRIZIONE INSERITA ------
    stop_currentword_timer()   # stop current work timer

    #print(f"trascrizione inserita:{text} - mode:{mode}")
    handeler.set_curent_transcript(text)

    # LOGs
    handeler.log_lastword(text, mode)

    # Prossima parola
    start_previousword_timer() #start prev timer
    next_word()


@eel.expose
def start_currentword_timer():
    handeler.start_currentword_timer()

@eel.expose
def start_previousword_timer():
    handeler.start_frompreviousword_timer()

@eel.expose
def stop_currentword_timer():
    handeler.stop_currentword_timer()

@eel.expose
def stop_previousword_timer():
    handeler.stop_frompreviousword_timer()

def close_callback(route, websockets):
    if not websockets:
        files = os.listdir(LOG_FOLDER)
        paths = [os.path.join(LOG_FOLDER, basename) for basename in files]
        latest_file = max(paths, key=os.path.getctime)
        with open(latest_file, "a") as log_file:
            log_file.write(f"\n\n\nSection time: {time()-start:.2f} sec\n")
        sys.exit()


init_GUI()

eel.init("www")
eel.start("index.html", mode='default', port=9564, close_callback=close_callback) #mode=default


# Cose Da Fare
#  - Caricare pagina progetto
#    crea un progetyto archivio
#    rispetta la struttura della cartella data
#
#  - Implementare salvataggio
#    per ora lo stato si salva in automatico e viene memorizzato tutto nel file transcription.dat
#
#  - Implementare AUTOCOMPLETION
#    mentre stai inserendo la trascrizione la lista delle opzioni viene filtrata (gia lo fa)
#    bisognerebbe allora implementare il "suggeritore" che permette di naviare la lista di opzioni con TAB o con le frecce
#    +++ Il file della keywordlist deve essere nella cartella www, senno il file html non lo vede
#
#  - Implementazione Timer 
#    per ora creiamo solo il log delle parole. questo logga per ogni parola il tempo necessario a trascriverla o validarla, e la modalità di interazione