from trocr.main import TrocrPredictor, main_train, main_validate
from trocr.dataset import ALSDataset
from trocr.util import load_processor
from utils import load_file, save_file
from torch.utils.data import DataLoader
import os
from rapidfuzz import fuzz, process
from tqdm import tqdm
from trocr.configs import constants

def predict_onedocument(als_filename, img_filename, batch_size=1, num_workers=0, words_dict=False, n_options=3, local_model=False, savefile=True):
    processor = load_processor()
    dataset = ALSDataset(als_filename, img_filename, processor)
    dataloader = DataLoader(dataset, batch_size, shuffle=False, num_workers=num_workers)

    predictor = TrocrPredictor(local_model)

    als_f = load_file(als_filename)

    # predictions = predictor.predict_from_aslDataloader(dataloader)
    predictions = predictor.predict_from_aslFile(als_f, img_filename)

    if words_dict:
        if os.path.exists(words_dict):
            dic_words = []
            with open(words_dict, "r") as w_f:
                for line in w_f.readlines():
                    dic_words.append(line.rstrip())
        else:
            words_dict = False

    for (doc_ids, line_ids, word_ids, generated_text), score in predictions:
        transcrips = als_f[doc_ids][line_ids][1][word_ids]

        if words_dict:
            other_options = _get_similar_transcripts(generated_text, dic_words, n_options=int(n_options)-1)
            all_generated_text = [generated_text]
            for extra_text in other_options:
                all_generated_text.append(extra_text[0])

        else:
            all_generated_text = [generated_text]

        for gen_txt in all_generated_text:
            if len(transcrips) == 1 and transcrips[0] == "":
                transcrips = [gen_txt]
            elif gen_txt not in transcrips:
                transcrips.append(gen_txt)
        
        als_f[doc_ids][line_ids][1][word_ids] = transcrips

    if savefile:
        save_file(als_f, als_filename)

    return als_f

def _get_similar_transcripts(text, dic_words, n_options=3, th=1):
    """
    Returns the n_options most similar entries to text in dic_words

    Each result is a tuple: (candidate, score, index)
    """
    results = process.extract(text, dic_words, scorer=fuzz.token_sort_ratio, limit=n_options, score_cutoff=th)
    return results

def train(local_model: bool = False):
    main_train(local_model, use_modifued_ds=True)



