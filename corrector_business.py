import os
from utils import load_file, save_file, resource_path
from PIL import Image, ImageDraw
import configs
import time
import datetime


class Handeler:

    def __init__(self, base_folder, document=""):
        self.base_folder = base_folder
        #self.documents_collection = documents_collection
        self.document = document
        self.current_doc_id = 0
        self.current_row_id = 0
        self.current_word_id = 0

        self.all_boxes = None
        self.all_transcripts_list = None

        self.current_doc_img = None
        self.current_row_img = None
        self.current_word_img = None

        self.line_segmentation_boundaries = {}

        # # TRANSCRIPTION FILE
        # if not os.path.exists(os.path.join(base_folder, configs.OUT_FOLDER)):
        #     os.makedirs(os.path.join(base_folder, configs.OUT_FOLDER))
        # self.out_transcription_file = os.path.join(base_folder, configs.OUT_FOLDER, configs.OUT_TRANSCRIPTION)
        # if os.path.exists(self.out_transcription_file):
        #     self.current_transcription = load_file(self.out_transcription_file)
        # else:
        #     self.current_transcription = {} # Page - line - word_position

        if document != "":
            self.reinit(document)
        

        # LOGGING
        self._currentword_timer_start = 0      # timer start
        self._frompreviousword_timer_start = 0 # timer start
        self._currentword_timer = 0            # timer value 
        self._frompreviousword_timer = 0       # timer value
        if not os.path.exists(os.path.join(base_folder, configs.LOG_FOLDER)):
            os.makedirs(os.path.join(base_folder, configs.LOG_FOLDER))

        now = datetime.datetime.now()
        self._current_wordstiming_log = f"{now.year}-{now.month}-{now.day}-{now.hour}-{now.minute}_{configs.LOG_WORDS_TIMING}"
        self._current_wordstiming_log = os.path.join(base_folder, configs.LOG_FOLDER, self._current_wordstiming_log)

        with open(self._current_wordstiming_log, "w", encoding='utf-8') as logwords_file:
            logwords_file.write("Doc_ID,line_ID,word_ID,transcript,mode,time_currentword_s, time_from_prevword_s\n")

    def reinit(self, document=""):
        #print("Document loaded: "+document)
        self.current_row_id = 0
        self.current_word_id = 0
        doc_id, _ = os.path.splitext(document)
        self.alignments_file = load_file(os.path.join(self.base_folder,configs.ALIGNMENTS_FOLDER,doc_id+".als"))

        self.documents_keys = list(self.alignments_file.keys())
        self.rows_keys = list(self.alignments_file[self.documents_keys[self.current_doc_id]].keys())

        # TRANSCRIPTION FILE
        if not os.path.exists(os.path.join(self.base_folder, configs.OUT_FOLDER)):
            os.makedirs(os.path.join(self.base_folder, configs.OUT_FOLDER))
        self.out_transcription_file = os.path.join(self.base_folder, configs.OUT_FOLDER, f"{doc_id}{configs.OUT_TRANSCRIPTION_EXTENSION}")
        if os.path.exists(self.out_transcription_file):
            self.current_transcription = load_file(self.out_transcription_file)
        else:
            self.current_transcription = {} # Page - line - word_position


    def _load_line_segmentations_info(self):
        try:
            self.current_doc_img = Image.open(os.path.join(self.base_folder, configs.DOC_FOLDER, self.documents_keys[self.current_doc_id]))
        except:
            try:
                self.current_doc_img = Image.open(os.path.join(self.base_folder, configs.DOC_FOLDER, self.documents_keys[self.current_doc_id]+".jpg"))
            except:
                try:
                    self.current_doc_img = Image.open(os.path.join(self.base_folder, configs.DOC_FOLDER, self.documents_keys[self.current_doc_id]+".png"))
                except:
                    raise Exception(f"No Documents image for {os.path.join(configs.DOC_FOLDER, self.documents_keys[self.current_doc_id])}") 

        self.line_segmentation_boundaries.clear()

        with open(os.path.join(self.base_folder, configs.LISE_SEGMENTATION_FOLDER, self.documents_keys[self.current_doc_id]), "r") as segm_file:
            for i, line in enumerate(segm_file.readlines()):
                if i != 0:
                    id,x,y,l,h = line.strip().split(",")
                    self.line_segmentation_boundaries[id] = (int(x),int(y),int(l),int(h))       

    def _iniziate_current_words_lists(self):
        self.all_boxes = self.alignments_file[self.documents_keys[self.current_doc_id]][self.rows_keys[self.current_row_id]][0]
        self.all_transcripts_list = self.alignments_file[self.documents_keys[self.current_doc_id]][self.rows_keys[self.current_row_id]][1]

    def start_currentword_timer(self):
        self._currentword_timer_start = time.time()

    def start_frompreviousword_timer(self):
        self._frompreviousword_timer_start = time.time()

    def stop_currentword_timer(self):
        self._currentword_timer = time.time() - self._currentword_timer_start

    def stop_frompreviousword_timer(self):
        if self._frompreviousword_timer_start != 0:
            self._frompreviousword_timer = time.time() - self._frompreviousword_timer_start

    
    def current_word(self):
        self._iniziate_current_words_lists()
        self.start_currentword_timer()
        #print(self.all_boxes[self.current_word_id])
        #print(self.all_transcripts_list[self.current_word_id])

    def next_word(self):
        if self.all_boxes is not None:
            self.current_word_id += 1

            # se fine righa
            if self.current_word_id == len(self.all_boxes):
                self.current_word_id = 0
                self.current_row_id += 1

                # se fine documento
                if self.current_row_id == len(self.rows_keys):
                    self.current_doc_id += 1
                    if self.current_doc_id == len(self.documents_keys):
                        #ultima parola della collezione
                        self.current_doc_id -= 1
                        self.current_row_id -= 1
                        self.current_word_id = len(self.all_boxes)-1
                    else:
                        self.current_row_id = 0
                        self.current_doc_id += 1

            self.current_word()        

    def prev_word(self):
        if self.all_boxes is not None:
            self.current_word_id -= 1

            # se inizio righa
            if self.current_word_id < 0: 
                self.current_row_id -= 1

                # se inizio documento
                if self.current_row_id < 0:
                    self.current_doc_id -= 1
                    if self.current_doc_id < 0:
                        #prima parola della collezione
                        self.current_doc_id += 1
                        self.current_row_id += 1
                        self.current_word_id = 0
                    else:
                        self.current_row_id = 0
                        self.current_doc_id -= 1
                else:
                    self._iniziate_current_words_lists()
                    self.current_word_id = len(self.all_boxes)-1


                    # Gerstisci piu documenti------------------------------------- !!!!!
            self.current_word()

    def get_transcript_list(self):
        return self.all_transcripts_list[self.current_word_id]
    
    def get_current_line_word_img(self, margin=25):
        row_id = self.rows_keys[self.current_row_id].split(".")[0]
        x,y,l,h = self.line_segmentation_boundaries[row_id]
        self.current_row_img = self.current_doc_img.crop((x, y-margin, x+l, y+h+margin))#(left, top, right, bottom)

        word_x0, word_x1 = self.all_boxes[self.current_word_id]
        self.current_word_img = self.current_row_img.crop((word_x0, margin, word_x1, h+margin))#(left, top, right, bottom)

        img_row_dr = ImageDraw.Draw(self.current_row_img) 
        img_row_dr.rectangle([(word_x0,margin),(word_x1,h+margin)], outline="green", width=5)

        #self.current_word_img.resize((120,120))

        self.current_row_img.save(resource_path(configs.ROW_IMAGE_INVIEW))
        self.current_word_img.save(resource_path(configs.WORD_IMAGE_INVIEW))


    def set_curent_transcript(self, transcript, dump=True):
        self.current_transcription.setdefault(self.current_doc_id, {}).setdefault(self.current_row_id, {})
        self.current_transcription[self.current_doc_id][self.current_row_id][self.current_word_id] = transcript

        if dump:
            save_file(self.current_transcription, self.out_transcription_file)

    def get_currentpage_transcription(self):
        transcription = ""
        if len(self.current_transcription) > 0:
            page_dic_trans = self.current_transcription[self.current_doc_id]

            pre_line_id = -1
            #for line_id, line_dic_trans in page_dic_trans.items():
            for line_id in sorted(page_dic_trans.keys()):
                line_dic_trans = page_dic_trans[line_id]
                while pre_line_id < line_id-1:
                        transcription += "...\n"    
                        pre_line_id += 1
                pre_word_id = -1
                for word_id in sorted(line_dic_trans.keys()):
                    while pre_word_id < word_id-1:
                        transcription += "**** "    
                        pre_word_id += 1
                    transcription += f"{line_dic_trans[word_id]} "
                    pre_word_id = word_id

                transcription.rstrip()
                transcription += '\n'
                pre_line_id = line_id

        return transcription

    
    def log_lastword(self, transcript, mode):
        #print("Doc_ID, line_ID, word_ID, transcript, mode, time(s)")
        with open(self._current_wordstiming_log, "a", encoding='utf-8') as logwords_file:
            oput_transcript = transcript
            # oput_transcript = oput_transcript.replace('"', '\\"')
            # oput_transcript = oput_transcript.replace("'", "\\'")
            logwords_file.write(f"{self.documents_keys[self.current_doc_id]},{self.rows_keys[self.current_row_id]},{self.current_word_id},'{oput_transcript}',{mode},{self._currentword_timer},{self._frompreviousword_timer}\n")
            
            #logwords_file.write(f"{self.current_doc_id},{self.current_row_id},{self.current_word_id},{transcript},{mode},{time_word}\n")
        #print(f"{self.current_doc_id},{self.current_row_id},{self.current_word_id},{transcript},{mode},{self._currentword_timer},{self._frompreviousword_timer}")
        





    def test(self):
        print("Test Print!")