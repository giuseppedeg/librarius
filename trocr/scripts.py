import os
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader
from transformers import TrOCRProcessor, VisionEncoderDecoderModel, get_scheduler
# from transformers import AdamW
from torch.optim import AdamW
from jiwer import wer, cer
from tqdm import tqdm
import time
from PIL import Image


from .configs import constants
from .context import Context
from .util import debug_print


def predict(
    processor: TrOCRProcessor, model: VisionEncoderDecoderModel, dataloader: DataLoader
) -> tuple[list[tuple[int, str]], list[float]]:
    output: list[tuple[int, str]] = []
    confidence_scores: list[tuple[int, float]] = []

    with torch.no_grad():
        model.eval()
        if constants.should_log:
            iterator = enumerate(tqdm(dataloader, disable=constants.tqdm_disable))
        else:
            iterator = enumerate(dataloader)
        for i, batch in iterator:
            #debug_print(f"Predicting batch {i+1}")
            inputs: torch.Tensor = batch["input"].to(constants.device)

            generated_ids = model.generate(inputs, return_dict_in_generate=True, output_scores = True)
            generated_text = processor.batch_decode(generated_ids.sequences, skip_special_tokens=True)

            ids = [t.item() for t in batch["idx"]]
            output.extend(zip(ids, generated_text))

            # Compute confidence scores
            batch_confidence_scores = get_confidence_scores(generated_ids)
            confidence_scores.extend(zip(ids, batch_confidence_scores))

    return output, confidence_scores


def predict_alsDataloader(
    processor: TrOCRProcessor, model: VisionEncoderDecoderModel, dataloader: DataLoader
) -> tuple[list[tuple[int, str, str, int, str]], list[float]]:
    output: list[tuple[int, str, str, int, str]] = []
    confidence_scores: list[tuple[int, float]] = []

    with torch.no_grad():
        model.eval()
        if constants.should_log:
            iterator = enumerate(tqdm(dataloader, disable=constants.tqdm_disable))
        else:
            iterator = enumerate(dataloader)
        for i, batch in iterator:
            #debug_print(f"Predicting batch {i+1}")
            inputs: torch.Tensor = batch["input"].to(constants.device)

            generated_ids = model.generate(inputs, return_dict_in_generate=True, output_scores = True)
            generated_text = processor.batch_decode(generated_ids.sequences, skip_special_tokens=True)

            ids = [t.item() for t in batch["idx"]]
            doc_ids = [t for t in batch["doc_id"]]
            line_ids = [t for t in batch["line_id"]]
            word_ids = [t.item() for t in batch["word_id"]]

            output.extend(zip(ids, doc_ids, line_ids, word_ids, generated_text))

            # Compute confidence scores
            batch_confidence_scores = get_confidence_scores(generated_ids)
            confidence_scores.extend(zip(ids, batch_confidence_scores))

    return output, confidence_scores


def predict_alsFile(
    processor: TrOCRProcessor, model: VisionEncoderDecoderModel, als_file, img_path
) -> tuple[list[tuple[int, str, str, int, str]], list[float]]:
    output: list[tuple[int, str, str, int, str]] = []
    confidence_scores: list[tuple[int, float]] = []

    doc_id_ = list(als_file.keys())[0]
    img  = Image.open(img_path).convert("RGB")

    img_data = []

    for line_id, line_data in als_file[doc_id_].items():
        line_bbox = line_data[2]
        for id_word, (bbox, trans) in enumerate(zip(line_data[0], line_data[1])):
            img_data.append({
                "word_bbox": bbox,
                "transcripts": trans,
                "word_id": id_word,
                "line_id": line_id,
                "line_bbox": line_bbox
            })

    with torch.no_grad():
        model.eval()
        if constants.should_log:
            iterator = enumerate(tqdm(img_data, disable=constants.tqdm_disable))
        else:
            iterator = enumerate(img_data)
       
        for i, img_info in iterator:
            #debug_print(f"Predicting batch {i+1}")
            word_bb = img_info["word_bbox"]
            line_bbox = img_info["line_bbox"]

            if word_bb[0] != word_bb[1] !=  word_bb[2] != word_bb[3] != 0:
                left = word_bb[0] + line_bbox[0]
                top = word_bb[1] + line_bbox[1]
                right = word_bb[2] + line_bbox[0]
                bottom = word_bb[3] + line_bbox[1]
                word_img = img.crop((left, top, right, bottom))

                # #word_img.save("word.png")
                
                inputs: torch.Tensor = processor(word_img, return_tensors="pt").pixel_values[0].to(constants.device)

                inputs = inputs.unsqueeze(0)
                # inputs: torch.Tensor = batch["input"].to(constants.device)

                generated_ids = model.generate(inputs, return_dict_in_generate=True, output_scores = True)   
                generated_text = processor.batch_decode(generated_ids.sequences, skip_special_tokens=True)
                
                ids = [i]
                doc_ids = [doc_id_]
                line_ids = [img_info["line_id"]]
                word_ids = [img_info["word_id"]]
                 # Compute confidence scores
                batch_confidence_scores = get_confidence_scores(generated_ids)
                confidence_scores.extend(zip(ids, batch_confidence_scores))

            else:
                generated_text = ""
                ids = [i]
                doc_ids = [doc_id_]
                line_ids = [img_info["line_id"]]
                word_ids = [img_info["word_id"]]

            output.extend(zip(ids, doc_ids, line_ids, word_ids, generated_text))

           

    return output, confidence_scores


def get_confidence_scores(generated_ids) -> list[float]:
    # Get raw logits, with shape (examples,tokens,token_vals)
    logits = generated_ids.scores
    logits = torch.stack(list(logits),dim=1)

    # Transform logits to softmax and keep only the highest (chosen) p for each token
    logit_probs = F.softmax(logits, dim=2)
    char_probs = logit_probs.max(dim=2)[0]

    # Only tokens of val>2 should influence the confidence. Thus, set probabilities to 1 for tokens 0-2
    mask = generated_ids.sequences[:,:-1] > 2
    char_probs[mask] = 1

    # Confidence of each example is cumulative product of token probs
    batch_confidence_scores = char_probs.cumprod(dim=1)[:, -1]
    return [v.item() for v in batch_confidence_scores]


# will return the accuracy but not print predictions
def validate(context: Context, print_wrong: bool = False) -> float:
    predictions, _ = predict(context.processor, context.model, context.val_dataloader)
    assert len(predictions) > 0

    correct_count = 0
    wrong_count = 0
    cer_val = 0
    wer_val = 0
    for id, prediction in predictions:
        label = context.val_dataset.get_label(id)
        path = context.val_dataset.get_path(id)

        cer_val += cer(label,prediction)
        wer_val += wer(label,prediction)

        if prediction == label:
            correct_count += 1
        else:
            wrong_count += 1
            if print_wrong:
                print(f"Predicted: \t{prediction}\nLabel: \t\t{label}\nPath: \t\t{path}")

    cer_val = cer_val/ len(predictions)
    wer_val = cer_val/ len(predictions)
    accuracy = correct_count / (len(predictions))

    if print_wrong:
        print(f"\nCorrect: {correct_count}\nWrong: {wrong_count}")

    return accuracy, wer_val, cer_val


def train(context: Context, num_epochs=5, log_folder="logs"):
    
    if not os.path.exists(log_folder):
        os.mkdir(log_folder)

    model = context.model
    optimizer = AdamW(model.parameters(), lr=constants.learning_rate)

    num_training_steps = num_epochs * len(context.train_dataloader)
    lr_scheduler = get_scheduler(
        "linear", optimizer=optimizer, num_warmup_steps=0, num_training_steps=num_training_steps
    )

    log_batch_file = open(os.path.join(log_folder, "loss_train_batch.txt"), "w")
    log_epoch_file = open(os.path.join(log_folder, "loss_train_epoch.txt"), "w")
    log_epoch_accuracy_file = open(os.path.join(log_folder, "acc_valid_epoch.txt"), "w")

    log_batch_file.write("batch,loss\n")
    log_epoch_file.write("epoch,loss\n")
    log_epoch_accuracy_file.write("epoch,accuracy,cer,wer\n")

    model.to(constants.device)
    model.train()

    for epoch in range(num_epochs):
        start_time = time.time()
        losses=0
        for j, batch in enumerate(context.train_dataloader):
            inputs: torch.Tensor = batch["input"].to(constants.device)
            labels: torch.Tensor = batch["label"].to(constants.device)

            outputs = model(pixel_values=inputs, labels=labels)
            loss = outputs.loss
            loss.backward()

            losses += loss

            optimizer.step()
            lr_scheduler.step()
            optimizer.zero_grad(set_to_none=True)

            debug_print(f"Epoch {1 + epoch}, Batch {1 + j}: {loss} loss")
            log_batch_file.write(f"{j},{loss}\n")
            log_batch_file.flush()
            del loss, outputs

        loss_epoch = losses/j
        log_epoch_file.write(f"{epoch},{loss_epoch}\n")
        log_epoch_file.flush()

        if len(context.val_dataloader) > 0:
            accuracy, wer, cer = validate(context)
            log_epoch_accuracy_file.write(f"{epoch},{accuracy},{cer},{wer}\n")
            log_epoch_accuracy_file.flush()
            print(f"\n---- Epoch {1 + epoch} ----\nAccuracy: {accuracy}, cer: {cer}, wer: {wer}\n")
            print(f"Time to train the epoch: {time.time()-start_time} seconds")
            print(f"Memory GPU allocated: {torch.cuda.max_memory_reserved(constants.device)/(1024 ** 3)} Gb")

    log_batch_file.close()
    log_epoch_file.close()
