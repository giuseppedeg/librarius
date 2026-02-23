import os
import shutil
from toolbox.word_segmenter import correct_segmentation_doc
from toolbox.line_segmenter import compute_seg_mask, line_segm
from toolbox.word_segmenter import word_segm_doc
from toolbox import trocr_manager as trocr_m
from utils import load_file, save_file, resource_path
from PIL import Image, ImageDraw
import configs
import time
import datetime

# import multiprocessing
# import subprocess
# from subprocess import Popen, CREATE_NEW_CONSOLE




DUMP = True # Save all modification in .als file 


class Handler:

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

        self.islogging = False
        # self.init_logging()
        
    def reinit(self, document=""):
        #print("Document loaded: "+document)
        self.current_row_id = 0
        self.current_word_id = 0
        self.document_img_name = document
        doc_id, _ = os.path.splitext(document)
        self.als_file_path = os.path.join(self.base_folder,configs.ALIGNMENTS_FOLDER,doc_id+".als")
        self.alignments_file = load_file(self.als_file_path)

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

    def reinit_als(self):
        self.alignments_file = load_file(self.als_file_path)
        self.all_transcripts_list = self.alignments_file[self.documents_keys[self.current_doc_id]][self.rows_keys[self.current_row_id]][1]

    def clean(self):
        self.__init__(self.base_folder)

        self.als_file_path = None
        self.alignments_file.clear()
        self.current_img_path = None
        self.current_transcription.clear()
        self.document_img_name = None
        self.documents_keys = None
        self.line_segmentation_boundaries.clear()
        self.out_transcription_file = None
        self.rows_keys = None
        self.all_transcripts_list = []

 
    def load_line_segmentations_info(self):
        try:
            self.current_img_path = os.path.join(self.base_folder, configs.DOC_FOLDER, self.documents_keys[self.current_doc_id])
            self.current_doc_img = Image.open(self.current_img_path)
        except:
            try:
                self.current_img_path = os.path.join(self.base_folder, configs.DOC_FOLDER, self.documents_keys[self.current_doc_id]+".jpg")
                self.current_doc_img = Image.open(self.current_img_path)
            except:
                try:
                    self.current_img_path = os.path.join(self.base_folder, configs.DOC_FOLDER, self.documents_keys[self.current_doc_id]+".png")
                    self.current_doc_img = Image.open(self.current_img_path)
                except:
                    raise Exception(f"No Documents image for {os.path.join(configs.DOC_FOLDER, self.documents_keys[self.current_doc_id])}") 

        self.line_segmentation_boundaries.clear()

        with open(os.path.join(self.base_folder, configs.LINE_SEGMENTATION_FOLDER, self.documents_keys[self.current_doc_id]), "r") as segm_file:
            for i, line in enumerate(segm_file.readlines()):
                if i != 0:
                    id,x,y,l,h = line.strip().split(",")
                    self.line_segmentation_boundaries[id] = (int(x),int(y),int(l),int(h))       

    def _iniziate_current_words_lists(self):
        self.all_boxes = self.alignments_file[self.documents_keys[self.current_doc_id]][self.rows_keys[self.current_row_id]][0]
        row_id = self.rows_keys[self.current_row_id].split(".")[0]
        (x0_l, y0_l, w_l, h_l) = self.line_segmentation_boundaries[row_id]

        for ind, box in enumerate(self.all_boxes):
            if len(box) == 2:
                self.all_boxes[ind] = [box[0], 0, box[1], h_l]
        self.all_transcripts_list = self.alignments_file[self.documents_keys[self.current_doc_id]][self.rows_keys[self.current_row_id]][1]

    def start_currentword_timer(self):
        self._currentword_timer_start = time.time()

    def start_frompreviousword_timer(self):
        self._frompreviousword_timer_start = time.time()

    def start_thinking_timer(self):
        self._thinking_timer = time.time()
        self._thinking_timer_isrunning = True

    def stop_currentword_timer(self):
        self._currentword_timer = time.time() - self._currentword_timer_start

    def stop_frompreviousword_timer(self):
        if self._frompreviousword_timer_start != 0:
            self._frompreviousword_timer = time.time() - self._frompreviousword_timer_start

    def stop_thinking_timer(self):
        if self._thinking_timer_isrunning:
            self._thinking_timer = time.time() - self._thinking_timer
        self._thinking_timer_isrunning = False
    
    def current_word(self):
        """
        Load the current word info: bounding-box, transcription, line image and word image
        """
        self._iniziate_current_words_lists()
        ## TIMERS - start currentword timer and stard thinking timer)
        self.start_currentword_timer()
        self.start_thinking_timer()
        #print(self.all_boxes[self.current_word_id])
        #print(self.all_transcripts_list[self.current_word_id])


    def delete_current_word(self, dump=DUMP):
        """
        Delete the current Bounding-box and transcription
        """
        self.all_transcripts_list.pop(self.current_word_id)
        self.all_boxes.pop(self.current_word_id)

        d_id = self.documents_keys[self.current_doc_id]
        r_id = self.rows_keys[self.current_row_id]

        if (d_id in self.current_transcription) and (r_id in self.current_transcription[d_id]):
            new_transcript = {}
            for trans_id in self.current_transcription[d_id][r_id]:
                if trans_id < self.current_word_id:
                    new_transcript[trans_id] = self.current_transcription[d_id][r_id][trans_id]
                if trans_id == self.current_word_id:
                    pass
                if trans_id > self.current_word_id:
                    new_transcript[trans_id-1] = self.current_transcription[d_id][r_id][trans_id]

            self.current_transcription[d_id][r_id] = new_transcript
        
        if self.current_word_id >= len(self.all_boxes):
            self.current_word_id -= 1

        if self.current_word_id < 0:
            empty_line = ([[0,0,0,0]], [[""]], self.alignments_file[d_id][r_id][2])
            self.alignments_file[d_id][r_id] = empty_line
            self.current_word_id = 0
       
        self.current_word()
    
        if dump:
            save_file(self.current_transcription, self.out_transcription_file) # .dat file
            save_file(self.alignments_file, self.als_file_path) # .als file
    

    def correct_segmentation(self, split_f=None):
        img_folder = os.path.join(self.base_folder, configs.DOC_FOLDER)
        correct_segmentation_doc(img_folder, self.als_file_path, self.out_transcription_file, 
                                 split_f=split_f,
                                 split=configs.SPLIT_CH, fuse=configs.FUSE_CH, create=configs.CREATE_CH)

        #reload document


    #### TRANSCRIPTION MODEL

    def clear_transcripts(self):
        """ 
        Remove all transcriprion option from the list of possible transcriptions
        """
        for row_id, row_data in self.alignments_file[os.path.splitext(self.document_img_name)[0]].items():
            for ind, _ in enumerate(row_data[1]):
                row_data[1][ind] = [""]
        save_file(self.alignments_file, self.als_file_path)


    def transcribe(self, htr_model, num_options, language):
        batch_size = configs.BATCH_SIZE
        num_workers = configs.NUM_WORKERS

        als_fname = self.als_file_path
        img_fname = self.current_img_path

        t = time.time()

        # running the code
        # self.alignments_file = trocr_m.predict_onedocument(als_fname, img_fname, batch_size=batch_size, num_workers=num_workers, local_model=htr_model, words_dict=language, n_options=num_options)
        trocr_m.predict_onedocument(als_fname, img_fname, batch_size=batch_size, num_workers=num_workers, local_model=htr_model, words_dict=language, n_options=num_options)
        
        self.log_transcribing_time(time.time()-t)

        # import threading
        # t1 = threading.Thread(target=trocr_m.predict_onedocument, args=(als_fname, img_fname, batch_size, num_workers, language, num_options, htr_model))
        # t1.start()
        # #t1.join()

        # t1 = multiprocessing.Process(target=trocr_m.predict_onedocument, args=(als_fname, img_fname, batch_size, num_workers, language, num_options, htr_model))
        # t1.start()
        # t1.join()

        # running python script:
        # process = Popen(["python", "predict_als.py", "--als_path", als_fname, "--img_path", img_fname, "--local_model", htr_model, "--language", language, "--n_options", num_options], creationflags=CREATE_NEW_CONSOLE)
        # process = Popen(["python", resource_path("predict_als.py"), "--als_path", als_fname, "--img_path", img_fname, "--local_model", htr_model, "--language", language, "--n_options", num_options])
        
        # running exe - decisamente piu lento
        # process = Popen(["predict.exe", "--als_path", als_fname, "--img_path", img_fname, "--local_model", htr_model, "--language", language, "--n_options", num_options], creationflags=CREATE_NEW_CONSOLE)
        
        # process.wait()  


    def apply_transcription(self, dump=True):
        """
        Apply the first transcription option as current transcription for each word. 
        If dump is True, save the transcription in .dat file
        
        :param dump: if True, save the transcription in .dat file
        """
        doc_id = os.path.splitext(self.document_img_name)[0]

        if doc_id not in self.current_transcription:
            self.current_transcription[doc_id] = {}

        for (id_line, line_con) in self.alignments_file[doc_id].items():
            if id_line not in self.current_transcription[doc_id]:
                self.current_transcription[doc_id][id_line] = {}
            for ind_word, word_transcripts in enumerate(line_con[1]):
                if word_transcripts[0] != "":
                    if ind_word not in self.current_transcription[doc_id][id_line]:
                        self.current_transcription[doc_id][id_line][ind_word] =  word_transcripts[0]
        
        if dump:
            save_file(self.current_transcription, self.out_transcription_file)


    def remove_transcription(self, dump=True):
        """
        Remove the current general transcription. 
        If dump is True, save the transcription in .dat file
        
        :param dump: if True, save the transcription in .dat file
        """
        doc_id = os.path.splitext(self.document_img_name)[0]

        self.current_transcription[doc_id] = {}

        if dump:
            save_file(self.current_transcription, self.out_transcription_file)

    ######## TRANSCRIPTION MODEL: END


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

    def to_word(self, word_id, line_id):
        self.current_word_id = word_id
        self.current_row_id = line_id

        self.current_word()

    def get_transcript_list(self):
        if len(self.all_transcripts_list) == 0 :
            return []
        return self.all_transcripts_list[self.current_word_id]
    
    def get_current_line_word_img(self, margin_line=(0,25,0,25), margin_word=(0,25,0,25)):
        row_id = self.rows_keys[self.current_row_id].split(".")[0]
        x,y,l,h = self.line_segmentation_boundaries[row_id]
        self.current_row_img = self.current_doc_img.crop((x-margin_line[0], y-margin_line[1], x+l+margin_line[2], y+h+margin_line[3]))#(left, top, right, bottom)
        img_row_dr = ImageDraw.Draw(self.current_row_img)
        self.current_row_img.size
        img_row_dr.rectangle([(margin_line[0],margin_line[1]),(l,h)], outline="blue", width=1)


        word_x0, word_y0, word_x1, word_y1 = self.all_boxes[self.current_word_id]
        if word_x0 == word_y0 == word_x1 == word_y1 == 0:
            self.current_word_img = Image.new("RGB", (1, 1), (255, 255, 255))
        else:
            self.current_word_img = self.current_row_img.crop((word_x0-margin_word[0]-margin_line[0], word_y0-margin_word[1]+margin_line[1], word_x1+margin_word[2], word_y1+margin_word[3]))#(left, top, right, bottom)

            img_row_dr.rectangle([(word_x0+margin_line[0],word_y0+margin_line[1]),(word_x1+margin_line[0],word_y1+margin_line[1])], outline="green", width=5)

        #self.current_word_img.resize((120,120))

        self.current_row_img.save(resource_path(configs.ROW_IMAGE_INVIEW))
        self.current_word_img.save(resource_path(configs.WORD_IMAGE_INVIEW))

    def get_currentword_transcript(self):

        # if exist validated transcript
        d_id = self.documents_keys[self.current_doc_id]
        r_id = self.rows_keys[self.current_row_id]

        if d_id in self.current_transcription:
            if r_id in self.current_transcription[d_id]:
                if self.current_word_id in self.current_transcription[d_id][r_id]:
                    return self.current_transcription[d_id][r_id][self.current_word_id]

        self.alignments_file
        if d_id in self.alignments_file:
            if r_id in self.alignments_file[d_id]:
                _, trans, _ = self.alignments_file[d_id][r_id]
                return trans[self.current_word_id][0]

        return ""

    def set_curent_transcript(self, transcript, dump=DUMP):
        d_id = self.documents_keys[self.current_doc_id]
        r_id = self.rows_keys[self.current_row_id]
        self.current_transcription.setdefault(d_id, {}).setdefault(r_id, {})
        self.current_transcription[d_id][r_id][self.current_word_id] = transcript

        if dump:
            save_file(self.current_transcription, self.out_transcription_file)

    def get_currentpage_transcription(self, html=False):
        transcription = ""
        if len(self.current_transcription) > 0:
            d_id = self.documents_keys[self.current_doc_id]
            r_id = self.rows_keys[self.current_row_id]
            page_dic_trans = self.current_transcription[d_id]

            pre_line_id = self.current_row_id-1
            #for line_id, line_dic_trans in page_dic_trans.items():
            for line_id in sorted(page_dic_trans.keys()):
                line_dic_trans = page_dic_trans[line_id]
                # while pre_line_id < line_id-1:
                #     transcription += "...\n"    
                #     pre_line_id += 1
                pre_word_id = -1
                pre_word_id = self.current_word_id-1
                for word_id in sorted(line_dic_trans.keys()):
                    while pre_word_id < word_id-1:
                        pre_word_id += 1
                        if html:
                            transcription += f'<div id_l={self.rows_keys.index(line_id)} id_w={pre_word_id} class="word-in-transcr" ondblclick ="click_on_transcript({self.rows_keys.index(line_id)},{pre_word_id})">'
                        transcription += "**** "
                        if html:
                            transcription += "</div>"
                    
                    if html:
                        transcription += f'<div id_l={self.rows_keys.index(line_id)} id_w={word_id} class="word-in-transcr" ondblclick ="click_on_transcript({self.rows_keys.index(line_id)},{word_id})">'    
                        transcription += f"{line_dic_trans[word_id]}</div>"
                    else:
                        transcription += f"{line_dic_trans[word_id]}"

                    pre_word_id = word_id

                transcription.rstrip()
                if html:
                    transcription += "<br />"
                else:
                    transcription += '\n'
                pre_line_id = line_id

        return transcription

    

    #### COLLECTION IMAGE MANAGEMENT
    
    def add_new_image(self, img_path, ls_model=None):
        ## UPLOAD IMAGE
        img = Image.open(img_path)
        img = img.convert("RGB")
        
        new_image_name = os.path.basename(img_path)
        new_image_name, ext = os.path.splitext(new_image_name)
        ok_image_name = f"{new_image_name}.jpg"
        dst_path = os.path.join(self.base_folder, configs.DOC_FOLDER, ok_image_name)
                
        ind = 2
        while(os.path.exists(dst_path)):
            ok_image_name = f"{new_image_name}_{ind}.jpg"
            dst_path = os.path.join(self.base_folder, configs.DOC_FOLDER, ok_image_name)
            ind += 1

        # Save Image File
        new_image_name, ext = os.path.splitext(ok_image_name)
        dst_path = os.path.join(self.base_folder, configs.DOC_FOLDER, ok_image_name)
        img.save(dst_path, "JPEG")

        ## SEGMENT IN LINE
        if ls_model:
            ls_model_path = ls_model
        else:
            ls_model_path = configs.CHECKPOINT_L_SEGMENTER
        compute_seg_mask(ls_model_path, dst_path, os.path.join(self.base_folder, configs.LINEMASKS_FOLDER))
        mask_path = os.path.join(self.base_folder, configs.LINEMASKS_FOLDER, f"{os.path.splitext(ok_image_name)[0]}.png")
        line_segm(dst_path, mask_path, os.path.join(self.base_folder, configs.LINE_SEGMENTATION_FOLDER), margin=configs.MARGIN_LINES)

        ## SEGMENT WORDS
        word_segm_doc(dst_path, os.path.join(self.base_folder, configs.LINE_SEGMENTATION_FOLDER), os.path.join(self.base_folder, configs.ALIGNMENTS_FOLDER), mode="L", bb_notinline=True)

        shutil.rmtree(os.path.join(self.base_folder, configs.LINEMASKS_FOLDER))

        return dst_path
        
    def delete_image(self, id_img):
        if hasattr(self, 'document_img_name') and (id_img == self.document_img_name):
            self.clean()

        id_img_name = os.path.splitext(id_img)[0]

        os.remove(os.path.join(self.base_folder, configs.DOC_FOLDER, id_img))
        os.remove(os.path.join(self.base_folder, configs.ALIGNMENTS_FOLDER, f"{id_img_name}.als"))
        os.remove(os.path.join(self.base_folder, configs.LINE_SEGMENTATION_FOLDER, f"{id_img_name}"))
        if os.path.exists(os.path.join(self.base_folder, configs.OUT_FOLDER, f"{id_img_name}.dat")):
            os.remove(os.path.join(self.base_folder, configs.OUT_FOLDER, f"{id_img_name}.dat"))
       
        #### LOGGING
    
    ######## COLLECTION IMAGE MANAGEMENT: END
    
    
    #### LOGGING

    def init_logging(self):
        self.islogging = True

        self._currentword_timer_start = 0      # timer start
        self._frompreviousword_timer_start = 0 # timer start
        self._currentword_timer = 0            # timer value - time from image view to confirm transcription
        self._frompreviousword_timer = 0       # timer value - time from previous transcript confirmation
        self._thinking_timer = 0               # timer value - time from image view to action
        self._thinking_timer_isrunning = False # True if thinking timer is running, False otherwise
        self._session_timer_start = time.time() # timer start of the session

        if not os.path.exists(os.path.join(self.base_folder, configs.LOG_FOLDER)):
            os.makedirs(os.path.join(self.base_folder, configs.LOG_FOLDER))

        now = datetime.datetime.now()
        self._current_wordstiming_log = f"{now.year}-{now.month}-{now.day}-{now.hour}-{now.minute}-{now.second}_{configs.LOG_WORDS_TIMING}"
        self._current_wordstiming_log = os.path.join(self.base_folder, configs.LOG_FOLDER, self._current_wordstiming_log)

        with open(self._current_wordstiming_log, "w", encoding='utf-8') as logwords_file:
            logwords_file.write("OP,Doc_ID,line_ID,word_ID,transcript,mode,time_currentword_s,time_from_prevword_s,thinking_time\n")
        
    def close_logging(self):
        self.islogging = False
        self._current_wordstiming_log = None

    def log_lastword(self, transcript, mode):
        if hasattr(self, '_current_wordstiming_log'):
            with open(self._current_wordstiming_log, "a", encoding='utf-8') as logwords_file:
                oput_transcript = transcript
                # oput_transcript = oput_transcript.replace('"', '\\"')
                logwords_file.write(f"tr,{self.documents_keys[self.current_doc_id]},{self.rows_keys[self.current_row_id]},{self.current_word_id},'{oput_transcript}',{mode},{self._currentword_timer},{self._frompreviousword_timer},{self._thinking_timer}\n")
            
    def log_transcribing_time(self, time):
        if hasattr(self, '_current_wordstiming_log'):
            with open(self._current_wordstiming_log, "a", encoding='utf-8') as logwords_file:
                logwords_file.write(f"HTR,{self.documents_keys[self.current_doc_id]},HTR-Transcription,,'',TRANSCRIBE,{time},,\n")

    def log_delete_word(self):
        if hasattr(self, '_current_wordstiming_log'):
            with open(self._current_wordstiming_log, "a", encoding='utf-8') as logwords_file:
                logwords_file.write(f"DEL,{self.documents_keys[self.current_doc_id]},{self.rows_keys[self.current_row_id]},{self.current_word_id},,DELETE,,,\n")        
        
    def log_session_time(self):
        if hasattr(self, '_current_wordstiming_log'):
            with open(self._current_wordstiming_log, "a", encoding='utf-8') as logwords_file:
                session_time = time.time() - self._session_timer_start
                logwords_file.write(f"SESSION,,,,'',SESSION_TIME,{session_time},,\n")
    
    ######## LOGGING: END

    def test(self):
        print("Test Print!")


