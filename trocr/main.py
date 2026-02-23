from PIL import Image
from torch.utils.data import DataLoader

from .configs import paths
from .configs import constants
from .context import Context
from .dataset import HCRDataset, HCRDataset_2, MemoryDataset
from .scripts import predict, predict_alsDataloader, predict_alsFile, train, validate
from .util import debug_print, init_model_for_training, load_model, load_processor


class TrocrPredictor:
    def __init__(self, use_local_model: bool = True):
        self.processor = load_processor()
        self.model = load_model(use_local_model)

    def predict_for_image_paths(self, image_paths: list[str]) -> list[tuple[str, float]]:
        images = [Image.open(path) for path in image_paths]
        return self.predict_images(images)

    def predict_images(self, images: list[Image.Image]) -> list[tuple[str, float]]:
        dataset = MemoryDataset(images, self.processor)
        dataloader = DataLoader(dataset, constants.batch_size)
        predictions, confidence_scores = predict(self.processor, self.model, dataloader)
        return zip([p[1] for p in sorted(predictions)], [p[1] for p in sorted(confidence_scores)])
    
    def predict_from_aslDataloader(self, dataloader: DataLoader)-> list[tuple[str, float]]:
        predictions, confidence_scores = predict_alsDataloader(self.processor, self.model, dataloader)
        return zip([(p[1], p[2], p[3], p[4]) for p in sorted(predictions)], [p[1] for p in sorted(confidence_scores)])
    
    def predict_from_aslFile(self, asl_file, img_path)-> list[tuple[str, float]]:
        predictions, confidence_scores = predict_alsFile(self.processor, self.model, asl_file, img_path)
        return zip([(p[1], p[2], p[3], p[4]) for p in sorted(predictions)], [p[1] for p in sorted(confidence_scores)])
    



def main_train(use_local_model: bool = False, use_modifued_ds: bool = False):
    processor = load_processor()
    if use_modifued_ds:
        train_dataset = HCRDataset_2("train", paths.dataset_path, processor)
        val_dataset = HCRDataset_2("valid", paths.dataset_path, processor)
    else:
        train_dataset = HCRDataset(paths.train_dir, processor)
        val_dataset = HCRDataset(paths.val_dir, processor)

    train_dataloader = DataLoader(train_dataset, constants.batch_size, shuffle=True, num_workers=constants.num_workers)
    val_dataloader = DataLoader(val_dataset, constants.batch_size, num_workers=constants.num_workers)

    model = load_model(use_local_model)
    init_model_for_training(model, processor)

    context = Context(model, processor, train_dataset, train_dataloader, val_dataset, val_dataloader)
    train(context, constants.train_epochs)
    debug_print(f"Saving model to {paths.model_path}...")
    model.save_pretrained(paths.model_path)


def main_validate(use_local_model: bool = True, use_modifued_ds: bool=False, test_on="valid"):
    processor = load_processor()
    if use_modifued_ds:
        val_dataset = HCRDataset_2(test_on, paths.dataset_path, processor)
    else:
        val_dataset = HCRDataset(paths.val_dir, processor)
    
    val_dataloader = DataLoader(val_dataset, constants.batch_size, shuffle=True, num_workers=constants.num_workers)

    model = load_model(use_local_model)

    context = Context(model, processor, None, None, val_dataset, val_dataloader)
    accuracy, wer, cer = validate(context, False)

    print(f"Accuracy: {accuracy}  -  wer: {wer}  -  cer: {cer}")
