from __future__ import division, print_function

import csv
import os
from pathlib import Path
import pickle

import torch
from PIL import Image
from torch.utils.data import Dataset
from transformers import TrOCRProcessor

from .configs import paths
from .configs import constants
from .util import debug_print


def load_csv_labels(csv_path: Path = paths.label_file) -> dict[str, str]:
    assert csv_path.exists(), f"Label csv at {csv_path} does not exist."

    labels: dict[str, str] = {}
    with open(csv_path, "r") as f:
        reader = csv.reader(f, delimiter=",")
        for row in reader:
            label = row[1]
            image_name = row[0]
            labels[image_name] = label

    return labels

def load_part_labels(type: str, part_path: Path = paths.dataset_path) -> dict[str, str]:
    part_file = part_path / f"{type}.part"
    assert part_file.exists(), f"Label part at {part_file} does not exist."

    labels: dict[str, str] = {}
    with open(part_file, "r") as f:
        
        for row in f.readlines():
            row = row.strip()
            parts = row.split(" ")
            label = parts[-1]

            #image_name = parts[0].split(",")[0]
            image_name = os.path.join("words", parts[0].split(",")[0])

            labels[image_name] = label

    return labels


def load_filepaths_and_labels(data_dir: Path = paths.train_dir) -> tuple[list, list]:
    sample_paths: list[str] = []
    labels: list[str] = []

    label_dict = load_csv_labels()

    for file_name in os.listdir(data_dir):
        path = data_dir / file_name

        if file_name.endswith(".jpg") or file_name.endswith(".png"):
            assert file_name in label_dict, f"No label for image '{file_name}'"
            label = label_dict[file_name]

            sample_paths.append(path)
            labels.append(label)

    debug_print(f"Loaded {len(sample_paths)} samples from {data_dir}")
    assert len(sample_paths) == len(labels)
    return sample_paths, labels


class HCRDataset(Dataset):
    def __init__(self, data_dir: Path, processor: TrOCRProcessor):
        self.image_name_list, self.label_list = load_filepaths_and_labels(data_dir)
        self.processor = processor

        self._max_label_len = max([constants.word_len_padding] + [len(label) for label in self.label_list])

    def __len__(self):
        return len(self.image_name_list)

    def __getitem__(self, idx):
        image = Image.open(self.image_name_list[idx]).convert("RGB")
        image_tensor: torch.Tensor = self.processor(image, return_tensors="pt").pixel_values[0]

        label = self.label_list[idx]
        label_tensor = self.processor.tokenizer(
            label,
            return_tensors="pt",
            padding=True,
            pad_to_multiple_of=self._max_label_len,
        ).input_ids[0]

        return {"idx": idx, "input": image_tensor, "label": label_tensor}

    def get_label(self, idx) -> str:
        assert 0 <= idx < len(self.label_list), f"id {idx} outside of bounds [0, {len(self.label_list)}]"
        return self.label_list[idx]

    def get_path(self, idx) -> str:
        assert 0 <= idx < len(self.label_list), f"id {idx} outside of bounds [0, {len(self.label_list)}]"
        return self.image_name_list[idx]


def load_filepaths_and_labels_2(type: str, data_dir: Path = paths.dataset_path) -> tuple[list, list]:
    sample_paths: list[str] = []
    labels: list[str] = []

    label_dict = load_part_labels(type=type)

    for file_name in label_dict:
        path = data_dir / file_name

        if file_name.endswith(".jpg") or file_name.endswith(".png"):
            assert file_name in label_dict, f"No label for image '{file_name}'"
            label = label_dict[file_name]

            sample_paths.append(path)
            labels.append(label)

    debug_print(f"Loaded {len(sample_paths)} samples from {data_dir} {type}")
    assert len(sample_paths) == len(labels)
    return sample_paths, labels


class HCRDataset_2(Dataset):
    def __init__(self, type: str, data_dir: Path, processor: TrOCRProcessor):
        self.type = type
        self.image_name_list, self.label_list = load_filepaths_and_labels_2(type, data_dir)
        self.processor = processor

        self._max_label_len = max([constants.word_len_padding] + [len(label) for label in self.label_list])

    def __len__(self):
        return len(self.image_name_list)

    def __getitem__(self, idx):
        image = Image.open(self.image_name_list[idx]).convert("RGB")
        image_tensor: torch.Tensor = self.processor(image, return_tensors="pt").pixel_values[0]

        label = self.label_list[idx]
        label_tensor = self.processor.tokenizer(
            label,
            return_tensors="pt",
            padding=True,
            pad_to_multiple_of=self._max_label_len,
        ).input_ids[0]

        return {"idx": idx, "input": image_tensor, "label": label_tensor}

    def get_label(self, idx) -> str:
        assert 0 <= idx < len(self.label_list), f"id {idx} outside of bounds [0, {len(self.label_list)}]"
        return self.label_list[idx]

    def get_path(self, idx) -> str:
        assert 0 <= idx < len(self.label_list), f"id {idx} outside of bounds [0, {len(self.label_list)}]"
        return self.image_name_list[idx]

class MemoryDataset(Dataset):
    def __init__(self, images: list[Image.Image], processor: TrOCRProcessor):
        self.images = images
        self.processor = processor

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        image = self.images[idx].convert("RGB")
        image_tensor: torch.Tensor = self.processor(image, return_tensors="pt").pixel_values[0]

        # create fake label
        label_tensor: torch.Tensor = self.processor.tokenizer(
            "",
            return_tensors="pt",
        ).input_ids[0]

        return {"idx": idx, "input": image_tensor, "label": label_tensor}


class ALSDataset(Dataset):
    def __init__(self, als_file_path: str, img_file_path: str, processor: TrOCRProcessor):
        self.als_file_path = als_file_path
        self.img_file_path = img_file_path
        self.processor = processor
        self.id_imagename = os.path.splitext(os.path.basename(img_file_path))[0]
        self.img = Image.open(img_file_path).convert("RGB")

        with open(als_file_path, 'rb') as handle:
            self.als_f = pickle.load(handle)

        self.img_data = []

        for line_id, line_data in self.als_f[self.id_imagename].items():
            line_bbox = line_data[2]
            for id_word, (bbox, trans) in enumerate(zip(line_data[0], line_data[1])):
                self.img_data.append({
                    "word_bbox": bbox,
                    "transcripts": trans,
                    "word_id": id_word,
                    "line_id": line_id,
                    "line_bbox": line_bbox
                })


    def __len__(self):
        return len(self.img_data)

    def __getitem__(self, idx):
        data = self.img_data[idx]

        word_bb = data["word_bbox"]
        line_bbox = data["line_bbox"]

        left = word_bb[0] + line_bbox[0]
        top = word_bb[1] + line_bbox[1]
        right = word_bb[2] + line_bbox[0]
        bottom = word_bb[3] + line_bbox[1]
        word_img = self.img.crop((left, top, right, bottom))

        #word_img.save("word.png")
        
        image_tensor: torch.Tensor = self.processor(word_img, return_tensors="pt").pixel_values[0]


        return {"idx": idx, "input": image_tensor, "doc_id": self.id_imagename,
                "line_id": data["line_id"], "word_id": data["word_id"]}
