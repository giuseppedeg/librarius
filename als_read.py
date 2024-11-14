import os
from utils import load_file, save_file

"""
THe script provide a CML interface to modify direclty a .als file
"""


ALIGNMENT_FILE = "data/alignments/001.als"
OUT_FOLDER = "data/new_alignments"
OUT_FILENAME = "new_001.als"

if not os.path.exists(OUT_FOLDER):
    os.makedirs(OUT_FOLDER)

aligns = load_file(ALIGNMENT_FILE)

kws_res = {}

to_end = False

for doc in aligns:
    kws_res[doc] = {}
    for line_name in aligns[doc]:
        kws_res[doc][line_name] = {}

        bbox = aligns[doc][line_name][0]
        transcripts = aligns[doc][line_name][1]

        kws_out = []

        for i, transc in enumerate(transcripts):
            new_tr_list = []
            if not to_end:
                print(f"doc:{doc} - line:{line_name} - word_id:{i}  - transcript_options:{transc}")
                choice = input("\nModifico? -s, -n, -f\n")
                if choice == "f":
                    to_end = True
                elif choice == "n":
                    if isinstance(transc, str):
                        new_tr_list.append(transc)
                    else:
                        new_tr_list += transc
                elif choice == "s":
                    new_list = input("Inserisci le opzioni separate da una virgola (,):\n")
                    new_tr_list = new_list.split(",")
                else:
                    print("La scelta deve essere una tra s/n/f")
                    exit()
            else:     
                if isinstance(transc, str):
                    new_tr_list.append(transc)
                else:
                    new_tr_list += transc

            kws_out.append(new_tr_list)
        
        kws_res[doc][line_name] = (bbox, kws_out)






save_file(kws_res, os.path.join(OUT_FOLDER,OUT_FILENAME))


print("Done!")