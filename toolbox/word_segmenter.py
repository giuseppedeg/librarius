import os
import shutil
import glob
from PIL import Image, ImageDraw
from skimage.filters import threshold_otsu
import numpy
import utils
import easyocr
import cv2
from tqdm import tqdm
import threading
import re


MODE = "L"
READER_LAN = ['en', 'it']
MIN_SIZE = 10
TEXT_THRESHOLD = 0.7


class CustomThread(threading.Thread):
    """
    Thread that handle return value of the run.
    The join return the falue of the function executed by the thread
    """
    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}, daemon=True, verbose=None):
        # Initializing the Thread class
        super().__init__(group, target, name, args, kwargs, daemon=daemon)
        self._return = None

    # Overriding the Thread.run function
    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args, **self._kwargs)

    def join(self):
        super().join()
        return self._return


def word_segm(imgs_dir, segfiles_dir, out_als_dir, mode="RGB", bb_notinline=True, save_imgs=False):
    """
    The method computes the segmentation at word level to the lines.
    It generates the .als files that are saved in the out_als_dir
    params:
       - mode: ['RGB'|'L'|'BW']  - defines the mode of the image
       - bb_notinline: [True|False]  - add the bb considered as 'not in line' for the easyocr segmenter
    """
    
    image_w_dir = os.path.join(os.path.dirname(imgs_dir), "wordsegmented_lines_img")

    if os.path.exists(out_als_dir):
        shutil.rmtree(out_als_dir)
    os.mkdir(out_als_dir)

    if save_imgs:
        if os.path.exists(image_w_dir):
            shutil.rmtree(image_w_dir)
        os.mkdir(image_w_dir)

    for doc_file in tqdm(os.listdir(imgs_dir), desc="Word Segm"):
        id_doc = os.path.splitext(doc_file)[0]
        imgdoc_path = os.path.join(imgs_dir, doc_file) 

        word_segm_doc(imgdoc_path, segfiles_dir, out_als_dir, mode=mode, bb_notinline=bb_notinline, save_imgs=save_imgs)


def word_segm_doc(doc_file_img, segfiles_dir, out_als_dir, mode="RGB", bb_notinline=True, save_imgs=False):
    """
    The method computes the segmentation at word level to the lines for a document.
    It generates the .als file that is saved in the out_als_dir
    params:
       - doc_file_img: path of the image to segment
       - mode: ['RGB'|'L'|'BW']  - defines the mode of the image
       - bb_notinline: [True|False]  - add the bb considered as 'not in line' for the easyocr segmenter
    """

    imgs_dir = os.path.dirname(doc_file_img)
    doc_file = os.path.basename(doc_file_img)
    id_doc = os.path.splitext(doc_file)[0]

    
    if save_imgs:
        image_w_dir = os.path.join(os.path.dirname(imgs_dir), "wordsegmented_lines_img")
        if not os.path.exists(image_w_dir):
            os.mkdir(image_w_dir)
        curr_outimg_folder = os.path.join(image_w_dir, os.path.splitext(doc_file)[0])
        os.mkdir(curr_outimg_folder)

    if id_doc in os.listdir(segfiles_dir):
        reader = easyocr.Reader(READER_LAN, gpu=True)
        id_doc = os.path.splitext(doc_file)[0]

        als_file = {}
        als_file[id_doc] = {}

        imgdoc_path = os.path.join(imgs_dir, doc_file) 
        segfile_path = os.path.join(segfiles_dir, id_doc)

        imgdoc = Image.open(imgdoc_path)
        imgdoc = imgdoc.convert("RGB")

        with open(segfile_path, "r") as segfile:
            for line in segfile.readlines()[1:]:
                id_line, x, y, w, h = line.rstrip().split(",")
                #id_line = int(id_line)
                bbox_line = [int(x), int(y), int(x)+int(w), int(y)+int(h)]
                bbox_list = []
                transcripts_list = []

                imgline = imgdoc.crop(bbox_line)
                #imgline.show()

                if mode == "L" or mode == "BW":
                    imgline = imgline.convert("L")
                if mode == "BW":
                    thresh = threshold_otsu( numpy.array(imgline))
                    imgline = imgline.point( lambda p: 255 if p > thresh else 0 )

                #segmentation = reader.readtext(numpy.array(imgline))
                segmentation = reader.detect(numpy.array(imgline), min_size=MIN_SIZE, text_threshold=TEXT_THRESHOLD)

                if save_imgs:
                    bb_img = imgline.copy()
                    bb_img = bb_img.convert("RGB")
                    draw = ImageDraw.Draw(bb_img)

                for bbox in segmentation[0][0]:
                    #[x_min, x_max, y_min, y_max]
                    x0, x1, y0, y1 = bbox
                    box = [int(x0), int(y0), int(x1), int(y1)]
                    bbox_list.append(box)
                    transcripts_list.append([''])
                    if save_imgs:
                        draw.rectangle(box, outline=(255,0,0), width=1)
                
                if len(segmentation[0][0]) == 0:
                    box = [0,0,0,0]
                    bbox_list.append(box)
                    transcripts_list.append([''])
                    

                if bb_notinline:
                    for bbox in segmentation[1][0]:
                        x0 = min(int(bbox[0][0]), int(bbox[2][0]))
                        x1 = max(int(bbox[0][0]), int(bbox[2][0]))
                        y0 = min(int(bbox[0][1]), int(bbox[2][1]))
                        y1 = max(int(bbox[0][1]), int(bbox[2][1]))
                        box = [x0, y0, x1, y1]

                        bbox_list.append(box)
                        transcripts_list.append([''])
                        if save_imgs:
                            draw.rectangle(box, outline=(0,0,255), width=1)

                # IF TRASCRIPTS LIST IS NOT EMPTY DECOMMENT!!!!
                # transcripts_list = [x for _, x in sorted(zip(bbox_list, transcripts_list), key=lambda pair: pair[0][0])]
                bbox_list = [x for x in sorted(bbox_list, key=lambda box: box[0])]

                als_file[id_doc][id_line] = (bbox_list, transcripts_list, bbox_line)

                if save_imgs:
                    n_img = str(len(os.listdir(curr_outimg_folder))).zfill(2)
                    bb_img.save(os.path.join(curr_outimg_folder, f"{n_img}.png"))
        
        als_path = os.path.join(out_als_dir, f"{id_doc}.als")
        utils.save_file(als_file, als_path)


def word_extracter(imgs_dir, segfiles_dir, als_dir, out_img_dir):
    """
    The methods extracts the images from the original images based on the segmentation in the als files.
    the images of word are saved in the out_img_dir
    params:
    """

    if os.path.exists(out_img_dir):
        shutil.rmtree(out_img_dir)
    os.mkdir(out_img_dir)

    for als_file in tqdm(os.listdir(als_dir), desc="Worda img saving"):
        pass


def crop_box_cv2(img_path, line_b_box, word_b_box, transcript, split="#"):
    window_name = "word_image"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 1)

    def click_event(event, x, y, flags, params):
        if event == cv2.EVENT_LBUTTONDOWN:
            # displaying the coordinates
            crop_border = x
            print(f"crop at {crop_border} pixels")

            curr_image_view = params[0].copy()
            cv2.line(curr_image_view, (crop_border, 0), (crop_border, curr_image_view.shape[0]), (0,0,255), 1) 
            cv2.imshow(window_name, curr_image_view)
            
            params.append(crop_border)
        
        # checking for right mouse clicks    
        if event==cv2.EVENT_RBUTTONDOWN:
            pass

    new_boxes = []
    doc_img = cv2.imread(img_path)

    start_col = line_b_box[0] + word_b_box[0]
    end_col = line_b_box[0] + word_b_box[2]
    start_row = line_b_box[1] + word_b_box[1]
    end_row = line_b_box[1] + word_b_box[3]

    all_transcripts = transcript.split(split)

    ind = 0
    while len(new_boxes) < len(all_transcripts)-1:
        word_img = numpy.zeros((end_row-start_row+40,end_col-start_col,3), dtype=numpy.uint8)
        word_img[0:end_row-start_row, 0:end_col-start_col] = doc_img[start_row:end_row, start_col:end_col]

        left_tr = all_transcripts[ind]
        right_tr = split.join(all_transcripts[ind+1:])

        font = cv2.FONT_HERSHEY_SIMPLEX
        org = (5, end_row-start_row+30)
        fontScale = 1
        color = (0, 255, 0)
        thickness = 2
        # Using cv2.putText() method
        word_img = cv2.putText(word_img, left_tr, org, font, fontScale, color, thickness, cv2.LINE_AA)

        cv2.imshow(window_name, word_img)

        par = [word_img]
        cv2.setMouseCallback(window_name, click_event, param=par)

        key_pressed = cv2.waitKey(0)

        #######
        ## Qui usiamo la interfaccia custom di openCV per permettere all'utente di cliccare sulla posizione di split del word box, in modo da segmentare correttamente la parola in due parti.
        ## L'utente deve cliccare con il tasto sinistro del mouse sulla posizione di
        ## split del word box, e poi premere invio per confermare la scelta. Se invece vuole saltare la parola senza segmentarla, deve premere direttamente invio senza cliccare.
        ##
        ## Per migliorare l'esperienza e la solidità dell'interfaccia, si potrebbe implementare l'interfaccia con metodi custom in modo da avere il controllo totale del processo

        cv2.destroyAllWindows()

        if len(par) > 1:
            cut_border = par[-1]
            #word_b_box = [cut_border, word_b_box[1], word_b_box[2], word_b_box[3]]
            new_box = [start_col-line_b_box[0], word_b_box[1], cut_border+start_col-line_b_box[0], word_b_box[3]]
            start_col = start_col+ cut_border
            new_boxes.append(new_box)
            ind += 1

        # if key_pressed == 13:
        #     #  ENTER
        #     print("Enter")
        
    new_boxes.append([start_col-line_b_box[0], word_b_box[1], word_b_box[2], word_b_box[3]])

    return new_boxes


def correct_segmentation_doc(imgs_dir, doc_file_als, doc_file_dat, split_f=None, split="#", fuse="@", create="?", splitBySpace=True):
    """
    6#The evidence ?of#the engagement,#consigned#to a portable 
    
    params:
       - doc_file_als: path of the .als image to segment
       - trs_dir: folder of the transcription file (.dat)
    
    """
    split_sym = [split]
    if splitBySpace:
        split_sym.append(" ")
        split_sym.append("\t")
        

    alss_dir = os.path.dirname(doc_file_als)
    trs_dir = os.path.dirname(doc_file_dat)
    als_file = os.path.basename(doc_file_als)
    id_doc = os.path.splitext(als_file)[0]

    img_path = os.path.join(imgs_dir, f"{id_doc}.png")
    for _ext_img in glob.glob( os.path.join(imgs_dir, f'{id_doc}.*') ):
        img_path = _ext_img

    als_f = utils.load_file(doc_file_als)
    dat_f = utils.load_file(doc_file_dat)

    for lineID_dat, dict_trans in dat_f[id_doc].items():
        dict_trans = dict(sorted(dict_trans.items()))
        dat_f[id_doc][lineID_dat] = dict_trans

    try:
        for lineID_dat, dict_trans in dat_f[id_doc].items():
            ## CREATE new b-boxes
            new_dict_trans = {}
            new_id_w_offset = 0
            for wordID_dat, transcript in dict_trans.items():
                if create in transcript:
                    if create == transcript[-1]:
                        # create next
                        transcript = transcript[:-1]
                        parts = transcript.split(create)
                        new_transcript = parts[-1]
                        curr_transcript = parts[0]
                        bb = als_f[id_doc][lineID_dat][0][wordID_dat+new_id_w_offset]

                        if wordID_dat+1+new_id_w_offset <= len(als_f[id_doc][lineID_dat][0]):
                            bb_next = als_f[id_doc][lineID_dat][0][wordID_dat+1+new_id_w_offset]
                            y0 = min(bb[1], bb_next[1])
                            y1 = max(bb[3], bb_next[3])
                            x1 = bb_next[0]
                        else:
                            y0 = bb[1]
                            y1 = bb[3]
                            x1= bb[2]+50

                        new_bb = [bb[2], y0, x1, y1]
                        new_trans = ['']

                        #ADD
                        als_f[id_doc][lineID_dat][0].insert(wordID_dat+1+new_id_w_offset, new_bb)
                        als_f[id_doc][lineID_dat][1].insert(wordID_dat+1+new_id_w_offset, new_trans)

                        new_dict_trans[wordID_dat+new_id_w_offset] = curr_transcript
                        new_id_w_offset += 1
                        new_dict_trans[wordID_dat+new_id_w_offset] = new_transcript
                    
                    elif create == transcript[0]:
                        # create prev
                        transcript = transcript[1:]
                        parts = transcript.split(create)
                        new_transcript = parts[0]
                        curr_transcript = parts[-1]
                        bb = als_f[id_doc][lineID_dat][0][wordID_dat+new_id_w_offset]

                        if wordID_dat-1+new_id_w_offset >= 0:
                            bb_prev = als_f[id_doc][lineID_dat][0][wordID_dat-1+new_id_w_offset]
                            x0 = bb_prev[2]
                            y0 = min(bb[1], bb_prev[1])
                            y1 = max(bb[3], bb_prev[3])
                        else:
                            x0 = bb[0]-50
                            y0 = bb[1]
                            y1 = bb[3]

                        new_bb = [x0, y0, bb[0], y1]
                        new_trans = ['']

                        #ADD
                        als_f[id_doc][lineID_dat][0].insert(wordID_dat+new_id_w_offset, new_bb)
                        als_f[id_doc][lineID_dat][1].insert(wordID_dat+new_id_w_offset, new_trans)

                        new_dict_trans[wordID_dat+new_id_w_offset] = new_transcript
                        new_id_w_offset += 1
                        new_dict_trans[wordID_dat+new_id_w_offset] = curr_transcript

                    else:
                        new_dict_trans[wordID_dat+new_id_w_offset] = transcript
                else:
                    new_dict_trans[wordID_dat+new_id_w_offset] = transcript


            dict_trans = new_dict_trans
            dat_f[id_doc][lineID_dat] = new_dict_trans

            ## FUSE new b-boxes
            new_dict_trans = {}
            new_id_w_offset = 0
            it_dic = iter(dict_trans.items())
            for wordID_dat, transcript in it_dic:
                if fuse in transcript:
                    if fuse == transcript[-1]:
                        # fuse with next:
                        while fuse == transcript[-1] and wordID_dat < len(dict_trans)-1:
                            transcript = transcript.replace(fuse, "")
                            if wordID_dat+1+new_id_w_offset <= len(als_f[id_doc][lineID_dat][0]):
                                if wordID_dat+1+new_id_w_offset < len(als_f[id_doc][lineID_dat][0]):
                                    bb = als_f[id_doc][lineID_dat][0][wordID_dat+new_id_w_offset]
                                    trans = als_f[id_doc][lineID_dat][1][wordID_dat+new_id_w_offset]
                                    bb_next = als_f[id_doc][lineID_dat][0][wordID_dat+1+new_id_w_offset]
                                    trans_next = als_f[id_doc][lineID_dat][1][wordID_dat+1+new_id_w_offset]

                                    new_bb = [bb[0], min(bb[1],bb_next[1]), bb_next[2], max(bb[3],bb_next[3])]
                                    new_trans = trans+trans_next

                                    del als_f[id_doc][lineID_dat][0][wordID_dat+new_id_w_offset]
                                    als_f[id_doc][lineID_dat][0][wordID_dat+new_id_w_offset] = new_bb
                                    del als_f[id_doc][lineID_dat][1][wordID_dat+new_id_w_offset]
                                    als_f[id_doc][lineID_dat][1][wordID_dat+new_id_w_offset] = new_trans

                                fuse_t = ""
                                if wordID_dat+1 in dict_trans:
                                    fuse_t = dict_trans[wordID_dat+1]
                                transcript += fuse_t
                                new_dict_trans[wordID_dat+new_id_w_offset] = transcript
                                if wordID_dat+new_id_w_offset+1 in dict_trans:
                                    wordID_dat += 1
                                    if wordID_dat < len(dict_trans)-1:
                                        next(it_dic)

                                new_id_w_offset -= 1
                            

                    elif fuse == transcript[0]:
                        # fuse with prev
                        transcript = transcript.replace(fuse, "")
                        if wordID_dat-1+new_id_w_offset >= 0:
                            bb = als_f[id_doc][lineID_dat][0][wordID_dat+new_id_w_offset]
                            trans = als_f[id_doc][lineID_dat][1][wordID_dat+new_id_w_offset]
                            bb_prev = als_f[id_doc][lineID_dat][0][wordID_dat-1+new_id_w_offset]
                            trans_prev = als_f[id_doc][lineID_dat][1][wordID_dat-1+new_id_w_offset]

                            new_bb = [bb_prev[0], min(bb[1],bb_prev[1]), bb[2], max(bb[3],bb_prev[3])]
                            new_trans = trans_prev+trans

                            als_f[id_doc][lineID_dat][0][wordID_dat+new_id_w_offset] = new_bb
                            del als_f[id_doc][lineID_dat][0][wordID_dat-1+new_id_w_offset]
                            als_f[id_doc][lineID_dat][1][wordID_dat+new_id_w_offset] = new_trans                        
                            del als_f[id_doc][lineID_dat][1][wordID_dat-1+new_id_w_offset]

                            fuse_t = ""
                            if wordID_dat-1 in dict_trans:
                                fuse_t = dict_trans[wordID_dat-1]

                            new_dict_trans[wordID_dat+new_id_w_offset-1] = fuse_t+transcript
                            new_id_w_offset -= 1
                        else:
                            new_dict_trans[0] = transcript

                    else:
                        new_dict_trans[wordID_dat+new_id_w_offset] = transcript
                else:
                    new_dict_trans[wordID_dat+new_id_w_offset] = transcript

            dict_trans = new_dict_trans
            dat_f[id_doc][lineID_dat] = new_dict_trans


            ## SPLIT new b-boxes
            new_dict_trans = {}
            new_bb_als = {}
            new_id_w_offset = 0

            for wordID_dat, transcript in dict_trans.items():
                for current_split in split_sym:
                    transcript = transcript.replace(current_split, split)

                if split in transcript:
                    bb = als_f[id_doc][lineID_dat][0][wordID_dat]
                    trans = als_f[id_doc][lineID_dat][1][wordID_dat]
                    line_bb = als_f[id_doc][lineID_dat][2]

                    if split_f:
                        new_bboxes = split_f(img_path, line_bb, bb, transcript, split)
                    else:
                    ## OpecnCV GUI
                        # thread the GUI to avoid crash
                        x = CustomThread(target=crop_box_cv2, args=(img_path, line_bb, bb, transcript, split))
                        x.start()
                        new_bboxes = x.join()

                    # new_bboxes = crop_box(img_path, line_bb, bb, transcript, split)
                    new_bb_als[wordID_dat] = new_bboxes

            new_id_w_offset_new = 0
            new_id_w_offset = 0
            for id in range(len(als_f[id_doc][lineID_dat][0])):
                if id in new_bb_als:
                    # transcripts_splitted = dict_trans[id].split(split)
                    transcripts_splitted = re.split(r'['+split_sym[0]+''.join(split_sym[1:])+']', dict_trans[id])
                    
                    bb_list = new_bb_als[id]
                    for id_offset, new_bb in enumerate(bb_list):    
                        if id_offset == 0:
                            als_f[id_doc][lineID_dat][0][id+new_id_w_offset_new] = new_bb
                        else:
                            als_f[id_doc][lineID_dat][0].insert(id+new_id_w_offset+id_offset, new_bb)
                            als_f[id_doc][lineID_dat][1].insert(id+new_id_w_offset+id_offset, trans)
                            new_id_w_offset_new += 1
                        
                        new_dict_trans[id+new_id_w_offset_new] = transcripts_splitted[id_offset]
                    new_id_w_offset += len(bb_list) -1
                else:
                    if id in dict_trans:
                        new_dict_trans[id+new_id_w_offset] = dict_trans[id]
                
            dict_trans = new_dict_trans
            dat_f[id_doc][lineID_dat] = new_dict_trans

            # IL SALVATTAGGIO AVVIENE ORA LINEA PER LINEA, IN MODO DA NON PERDERE TUTTO IL LAVORO IN CASO DI CRASH DURANTE IL PROCESSO
            # SI POTREBBE MODIFICARE PER SALVARE DOPO OGNI PAROLA, MA POTREBBE ESSERE PIU LENTO
            utils.save_file(als_f, doc_file_als)
            utils.save_file(dat_f, doc_file_dat)
    
    except SegmentationCancelled as e:
        print(f"Error in line {lineID_dat} of doc {id_doc}: {e}")
        # utils.save_file(als_f, doc_file_als)
        # utils.save_file(dat_f, doc_file_dat)  
        return False

    # save
    # utils.save_file(als_f, doc_file_als)
    # utils.save_file(dat_f, doc_file_dat)  




### Error Exceptions ###
class SegmentationCancelled(Exception):
    pass


if __name__ == "__main__":
    # word_segm(IMG_DIR, SEGFILES_DIR, ALS_DIR, mode=MODE, save_imgs=False)

    #word_extracter(IMG_DIR, SEGFILES_DIR, ALS_DIR)

    correct_segmentation_doc("data\\doc_img", 
                             "data\\alignments\\002_080_001.als", 
                             "data\\outs\\002_080_001.dat", split="#", fuse="@", create="?")

    print()