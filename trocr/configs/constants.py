import torch

device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")

num_workers = 8
should_log = False

batch_size = 12
train_epochs = 1
word_len_padding = 8  # will be overriden if the dataset contains labels longer than the constant
learning_rate = 5e-6

tqdm_disable = False