import os
import sys
import io
import wx
import configs as C
import eel
from corrector_business import Handler
import configs
from time import sleep, time
from utils import resource_path
import json
import threading
import socket

import base64
import cv2
import numpy

from toolbox.word_segmenter import SegmentationCancelled

BASE_PATH = os.path.split(sys.argv[0])[0]
#BASE_PATH = os.getcwd()

# Determina se l'app è "congelata" (EXE) o script
if getattr(sys, 'frozen', False):
    BASE_PATH = os.path.dirname(sys.executable)
    import pyi_splash  # splash screen per PyInstaller
else:
    BASE_PATH = os.path.dirname(os.path.abspath(__file__))
    # BASE_PATH = os.path.abspath(".")
print(f"BASE_PATH: {BASE_PATH}")


#### LOGGING MAIN
import logging
# logfile = io.StringIO()
# sys.stdout = logfile
# sys.stderr = logfile

logging.basicConfig(
    filename=os.path.join(BASE_PATH, 'app.log'),
    filemode='w',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class StdoutToLog:
    def write(self, msg):
        if msg.strip():
            logging.info(msg.strip())
    def flush(self):
        pass

class StderrToLog:
    def write(self, msg):
        if msg.strip():
            logging.error(msg.strip())
    def flush(self):
        pass

sys.stdout = StdoutToLog()
sys.stderr = StderrToLog()
######## LOGGING_END 


handler = Handler(os.path.join(BASE_PATH,"data"))

CONFIGS_JS_FILEPATH = resource_path(os.path.join("www","data","configs.js"))
KLIST_JS_FILEPATH = resource_path(os.path.join("www","data","keyword_list.js"))
LAN_FILE = resource_path(os.path.join("dicts","eng"))
DOCUMENT_IMAGE_FOLDER = os.path.join(BASE_PATH,"data","doc_img")
LS_MODEL_FOLDER = os.path.join(BASE_PATH,"models","line_segmenter")
HTR_MODEL_FOLDER = os.path.join(BASE_PATH,"models","trocr")
LOG_FOLDER = os.path.join(BASE_PATH,"data","logs")

start = time()

def init_GUI():
    # Models options
    with open(CONFIGS_JS_FILEPATH, "w") as document_js_file:
        document_js_file.write("const all_documents = [")
        for page_img in os.listdir(DOCUMENT_IMAGE_FOLDER):
            document_js_file.write(f'"{page_img}",')
        document_js_file.write("]")

        document_js_file.write("\n\nconst all_ls_models = [")
        ls_models = os.listdir(LS_MODEL_FOLDER)
        ls_models.sort()
        for model in ls_models:
            document_js_file.write(f'"{"/".join([LS_MODEL_FOLDER.replace(os.sep, "/"), model])}",')
        document_js_file.write("]")

        document_js_file.write("\n\nconst all_trocr_models = [")
        for model in os.listdir(HTR_MODEL_FOLDER):
            document_js_file.write(f'"{"/".join([HTR_MODEL_FOLDER.replace(os.sep, "/"), model])}",')
        document_js_file.write("]")

    # dict list
    with open(KLIST_JS_FILEPATH, "w") as klist_js_file:
        with open(LAN_FILE, "r") as klist_in:
            klist_js_file.write("var all_keywords = [")
            for line in klist_in.readlines():
                klist_js_file.write(f'"{line.rstrip()}",')
            klist_js_file.write("]")

    if getattr(sys, 'frozen', False):
        pyi_splash.close()
        pass
        

@eel.expose
def get_next_row_image():
    print("next_row")

@eel.expose
def get_prev_row_image():
    print("prev_row")


def _update_view(list_tr):
    transcription = handler.get_currentpage_transcription(html=True)
    word_transcript = handler.get_currentword_transcript()
    eel.update_transcription_area(transcription)
    eel.update_transcript_input(word_transcript)
    eel.show_transcripts_list(list_tr)
    eel.show_current_word_img(configs.WORD_IMAGE_INVIEW.replace("www", "."))
    eel.show_current_line_img(configs.ROW_IMAGE_INVIEW.replace("www", "."))

@eel.expose
def release_document():
    """Close document and go to Home page"""
    handler.log_session_time()
    handler.close_logging()

    handler.clean()

@eel.expose
def load_document(doc=None):
    """Load document and show the first line and word"""
    if not handler.islogging:
        handler.init_logging()

    if doc == None:
        doc = handler.document_img_name
    handler.reinit(doc)

    handler.load_line_segmentations_info()
    handler.current_word()
    list_tr = handler.get_transcript_list()
    handler.get_current_line_word_img(margin_line=configs.MARGIN_LINE, margin_word=configs.MARGIN_WORD)

    _update_view(list_tr)   

    
@eel.expose
def next_word():
    handler.next_word()
    list_tr = handler.get_transcript_list()
    handler.get_current_line_word_img(margin_line=configs.MARGIN_LINE, margin_word=configs.MARGIN_WORD)

    sleep(0.05)  # otherwise problem in list on page
    _update_view(list_tr)


@eel.expose
def prev_word():
    handler.prev_word()
    list_tr = handler.get_transcript_list()
    handler.get_current_line_word_img(margin_line=configs.MARGIN_LINE, margin_word=configs.MARGIN_WORD)

    _update_view(list_tr)

@eel.expose
def to_word(word_id, line_id):
    handler.to_word(word_id, line_id)

    list_tr = handler.get_transcript_list()
    handler.get_current_line_word_img(margin_line=configs.MARGIN_LINE, margin_word=configs.MARGIN_WORD)

    #sleep(0.05)
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
        NEXT -> click on arrow left key 
        PREV -> click on arrow right key 
    """
    
    text = text.strip()
    text = text.replace(" ", configs.SPLIT_CH)

    # SALVA TRASCRIZIONE INSERITA ------
    stop_currentword_timer()   # stop current work timer
    stop_thinking_timer()     # stop thinking timer if it is running, otherwise do nothing
    stop_previousword_timer()  # stop previous word timer if it is running, otherwise do nothing

    #print(f"trascrizione inserita:{text} - mode:{mode}")
    handler.set_curent_transcript(text)

    # LOGs
    handler.log_lastword(text, mode)

    start_previousword_timer() #start prev timer

    # next_word()


#### TIMERS
@eel.expose
def start_currentword_timer():
    handler.start_currentword_timer()

@eel.expose
def start_previousword_timer():
    handler.start_frompreviousword_timer()

@eel.expose
def stop_currentword_timer():
    handler.stop_currentword_timer()

@eel.expose
def stop_previousword_timer():
    handler.stop_frompreviousword_timer()

@eel.expose
def start_thinking_timer():
    handler.start_thinking_timer()

@eel.expose
def stop_thinking_timer():
    handler.stop_thinking_timer()

######## TIMERS:END


@eel.expose
def delete_current_word():
    handler.delete_current_word()
    list_tr = handler.get_transcript_list()
    handler.get_current_line_word_img(margin_line=configs.MARGIN_LINE, margin_word=configs.MARGIN_WORD)

    handler.log_delete_word()
    sleep(0.05)  # otherwise problem in list on page
    _update_view(list_tr)


#### CORRECTION OPERATIONS
@eel.expose
def correct_segmentation():
    current_word_id = handler.current_word_id
    current_row_id = handler.current_row_id

    for w_id, w in handler.current_transcription[handler.documents_keys[0]][handler.rows_keys[handler.current_row_id]].items():
        if w_id < handler.current_word_id:
            if C.FUSE_CH in w:
                current_word_id -= 1
            if C.CREATE_CH in w:
                current_word_id += 1
            current_word_id += w.count(C.SPLIT_CH)

    handler.correct_segmentation(split_f=crop_box_eel)
    load_document()
    to_word(current_word_id, current_row_id)


# Variabile globale temporanea per lo split
user_response = {"x": None, "ready": False, "cancel": False}
@eel.expose
def return_split_value(x, cancel=False):
    global user_response
    user_response["x"] = x
    user_response["ready"] = True
    user_response["cancel"] = cancel


def get_user_split_point(word_img, transcript, all_transcript_str):
    """
    Traduce l'immagine in base64 e chiama la GUI.
    Questa è l'unica funzione che tocca Eel.
    """
    global user_response
    user_response = {"x": None, "ready": False, "cancel": False} # Reset

    _, buffer = cv2.imencode('.png', word_img)
    img_base64 = base64.b64encode(buffer).decode('utf-8')
    
    eel.open_crop_popup(img_base64, transcript, all_transcript_str)()

    # Blocchiamo Python finché la variabile non cambia
    while not user_response["ready"]:
        eel.sleep(0.2)

    if user_response["cancel"]:
        raise SegmentationCancelled("Segmentation Correction Cancelled by User")

    return user_response["x"]


def crop_box_eel(img_path, line_b_box, word_b_box, transcript, split="#"):
    """
    Split the word bounding-box in two, according to the user input, and update the transcript list accordingly.
    It uses Eel GUI to get the user input, so it is non-blocking and does not cause crashes.
    
    :param img_path: Description
    :param line_b_box: Description
    :param word_b_box: Description
    :param transcript: Description
    :param split: Description
    """
    new_boxes = []
    doc_img = cv2.imread(img_path)

    start_col = line_b_box[0] + word_b_box[0]
    end_col = line_b_box[0] + word_b_box[2]
    start_row = line_b_box[1] + word_b_box[1]
    end_row = line_b_box[1] + word_b_box[3]

    all_transcripts = transcript.split(split)
    ind = 0

    while len(new_boxes) < len(all_transcripts) - 1 and ind < len(all_transcripts):
        black_lines = 0  # 40 if we insert text in image (cv2.putText)
        word_img = numpy.zeros((end_row-start_row+black_lines, end_col-start_col, 3), dtype=numpy.uint8)
        word_img[0:end_row-start_row, 0:end_col-start_col] = doc_img[start_row:end_row, start_col:end_col]
        
        left_tr = all_transcripts[ind]
        all_transcript_str = " ".join(all_transcripts[ind:])

        # Insert text transcription ## Better show in HTML
        # font = cv2.FONT_HERSHEY_SIMPLEX
        # org = (5, end_row-start_row+30)
        # fontScale = 1
        # color = (0, 255, 0)
        # thickness = 2
        # word_img = cv2.putText(word_img, left_tr, org, font, fontScale, color, thickness, cv2.LINE_AA)


        # 2. CHIAMATA ALL'INTERFACCIA (Separazione)
        cut_border = get_user_split_point(word_img, left_tr, all_transcript_str)

        # 3. Elaborazione dei risultati (Business Logic)
        if cut_border is not None: 
            if cut_border not in [0, end_col-start_col]:
                new_box = [
                    start_col - line_b_box[0], 
                    word_b_box[1], 
                    cut_border + start_col - line_b_box[0], 
                    word_b_box[3]
                ]
                start_col = start_col + cut_border
                new_boxes.append(new_box)
            ind += 1

    
    if len(new_boxes) > 0:
        # Last Box
        new_boxes.append([start_col - line_b_box[0], word_b_box[1], word_b_box[2], word_b_box[3]])

    return new_boxes

######## CORRECTION OPERATIONS:END


@eel.expose
def clear_transcripts():
    handler.clear_transcripts()
    list_tr = handler.get_transcript_list()
    _update_view(list_tr)


@eel.expose
def apply_transcription():
    handler.apply_transcription()
    list_tr = handler.get_transcript_list()
    _update_view(list_tr)


@eel.expose
def transcribe(htr_model, num_options, language):
    print(htr_model, num_options, language)
    # p1 = multiprocessing.Process(target=running_process, args=(handler, htr_model, num_options, resource_path(os.path.join(configs.KEYWORDS_DICTS_FOLDER,language))))
    p1 = threading.Thread(target=running_process, args=(htr_model, num_options, resource_path(os.path.join(configs.KEYWORDS_DICTS_FOLDER,language))))
    p1.daemon = True
    p1.start()


def running_process(htr_model, num_options, language):
    handler.transcribe(htr_model, num_options, language)
    # reinit the interface and show the results
    handler.reinit_als()
    list_tr = handler.get_transcript_list()
    _update_view(list_tr)
    eel.hide_modal_create_trans()


#### MANAGE DOCUMENTS
@eel.expose
def uploadImage(ls_model, wildcard="*"):
    app = wx.App(None)
    style = wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.DIALOG_NO_PARENT
    dialog = wx.FileDialog(None, 'Open', wildcard=wildcard, style=style)
    # dialog.SetIcon(wx.Icon("www/images/tools-ico/icon.icon", wx.BITMAP_TYPE_ICO))
    if dialog.ShowModal() == wx.ID_OK:
        path = dialog.GetPath()
        path = handler.add_new_image(path, ls_model)
    else:
        path = None
    dialog.Destroy()
    eel.hide_modal_load_document()

    return os.path.basename(path)

@eel.expose
def deleteImage(id_img):
    handler.delete_image(id_img)

    #_update_view([])   
    eel.show_transcripts_list([])

######## MANAGE DOCUMENTS: END



#### CLOSE CALLBACK
def close_callback(route, websockets):
    if not websockets:
        handler.log_session_time()

        # files = os.listdir(LOG_FOLDER)
        # paths = [os.path.join(LOG_FOLDER, basename) for basename in files]
        # latest_file = max(paths, key=os.path.getctime)
        # with open(latest_file, "a") as log_file:
        #     log_file.write(f"\n\n\nSection time: {time()-start:.2f} sec\n")

        sys.exit()



if __name__ == "__main__":
    print(f".\n\n{'='*40}\nStarting application...")
    with open("configs", "r") as json_configs_f:
        json_configs = json.load(json_configs_f)
    if "port" in json_configs:
        configs.PORT = json_configs["port"]
    if "margin_line" in json_configs:
        configs.MARGIN_LINE = json_configs["margin_line"]
    if "margin_word" in json_configs:
        configs.MARGIN_WORD = json_configs["margin_word"]
    if "margin_lines" in json_configs:
        configs.MARGIN_LINES = json_configs["margin_lines"]
    if "h_word_inview" in json_configs:
        configs.H_WORD_INVIEW = json_configs["h_word_inview"]
    if "split_ch" in json_configs:
        configs.SPLIT_CH = json_configs["split_ch"]
    if "fuse_ch" in json_configs:
        configs.FUSE_CH = json_configs["fuse_ch"]
    if "create_ch" in json_configs:
        configs.CREATE_CH = json_configs["create_ch"]
    if "mode" in json_configs:
        configs.MODE = json_configs["mode"]

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    if s.connect_ex(('localhost', configs.PORT)) != 0:

        init_GUI()

        # eel.init(os.path.join(base_dir, 'www'))
        eel.init( 'www')
        eel.start("index.html", mode=configs.MODE, port=configs.PORT, close_callback=close_callback) #mode=default | chrome



# Cose Da Fare
#  - Gestire Multiple collezioni
#    Permettere di gestire piu collezioni dalla stessa interfaccia.
#    dal menu dove ora ci sono i documenti, bisognerebbe prima scegliere la collezione
#    in questo modo poi possiamo gestire il training per le diverse collezioni (generando modelli diversi per ogni collezione)    
#
#  - Implementare salvataggio
#    per ora lo stato si salva in automatico e viene memorizzato tutto nel file transcription.dat
#
#
#  - Quando una linea si svuota di tutti i suoni BB, dovrebbe essere eliminata dal file als