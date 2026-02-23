from transformers import TrOCRProcessor, VisionEncoderDecoderModel

from .configs import paths
from .configs import constants


def load_processor() -> TrOCRProcessor:
    return TrOCRProcessor.from_pretrained(paths.trocr_repo)


def load_model(from_disk) -> VisionEncoderDecoderModel:
    """
    params:
      - from_disk: if is equal to False, it is downloaded the custom model from repository
                   if is a path to a local model, the local model is loaded
    """
    if from_disk:
        assert from_disk, f"No model existing at {from_disk}"
        model: VisionEncoderDecoderModel = VisionEncoderDecoderModel.from_pretrained(from_disk)
        debug_print(f"Loaded local model from {from_disk}")
    else:
        model: VisionEncoderDecoderModel = VisionEncoderDecoderModel.from_pretrained(paths.trocr_repo)
        debug_print(f"Loaded pretrained model from huggingface ({paths.trocr_repo})")

    debug_print(f"Using device {constants.device}.")
    model.to(constants.device)
    return model


def init_model_for_training(model: VisionEncoderDecoderModel, processor: TrOCRProcessor):
    model.config.decoder_start_token_id = processor.tokenizer.cls_token_id
    model.config.pad_token_id = processor.tokenizer.pad_token_id
    model.config.vocab_size = model.config.decoder.vocab_size


def debug_print(string: str):
    if constants.should_log:
        print(string)
