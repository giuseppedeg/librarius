import os

# Librarius sw 
PORT = 9565
MODE = "chrome"

DOC_FOLDER = "doc_img"
ALIGNMENTS_FOLDER = "alignments"
LINE_SEGMENTATION_FOLDER = "line_segmentation"
LINEMASKS_FOLDER = "line_segmentation_masks"

LOG_FOLDER = "logs"
LOG_WORDS_TIMING = "words_timing.csv"

OUT_FOLDER = "outs"
OUT_TRANSCRIPTION_EXTENSION = ".dat"

KEYWORDS_DICTS_FOLDER = "dicts"

ROW_IMAGE_INVIEW = os.path.join("www","images","current_row.png")
WORD_IMAGE_INVIEW =  os.path.join("www","images","current_word.png")

H_WORD_INVIEW = 150

#  line segmenter
CHECKPOINT_L_SEGMENTER = os.path.join("models\line_segmenter","0195.pth")
MARGIN_LINES = (20,0,20,10) # (l,t,r,b)
MARGIN_LINE = (10,0,10,0)  # Margin in GUI
MARGIN_WORD = (10,0,10,0)  # Margin in GUI



# Word Segmentation COrrection
SPLIT_CH = "#"
FUSE_CH = "@"
CREATE_CH = "?"

# automatic transcription
BATCH_SIZE = 1 
NUM_WORKERS = 1 
LOCAL_MODEL = False 
