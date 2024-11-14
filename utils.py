import pickle 
import sys
import os

def save_file(all_alignments, file_name): 
    with open(file_name, 'wb') as handle:
        pickle.dump(all_alignments, handle, protocol=pickle.HIGHEST_PROTOCOL)

def load_file(file_name):
    with open(file_name, 'rb') as handle:
        all_alignments = pickle.load(handle)
    return all_alignments    


def resource_path(relative_path):      
    """ Get absolute path to resource, works for dev and for PyInstaller """       
    try: # PyInstaller creates a temp folder and stores path in _MEIPASS           
        base_path = sys._MEIPASS       
    except Exception:           
        base_path = os.path.abspath(".")       
    return os.path.join(base_path, relative_path)
