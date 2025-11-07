import gc

import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional
from torch.nn import CrossEntropyLoss
from torch.optim import Adam
import fist
from transformers import GPT2TokenizerFast, GPTNeoConfig, GPTNeoForCausalLM, LongformerConfig, LongformerTokenizer
from torch.utils.data import DataLoader, Dataset, random_split
from torch.nn.utils.rnn import pad_sequence
from torch.cuda.amp import autocast, GradScaler
from torch.utils.checkpoint import checkpoint
import time
total_dataset = pd.read_csv("training_template.csv", encoding ="latin1")   # complete dataset- 90% for training and 10% for validation
# data_validation = pd.read_csv("validation_google_synthetic_persona_chat.csv")
tokenizer = LongformerTokenizer.from_pretrained("allenai/longformer-base-4096")
tokenizer.pad_token = tokenizer.eos_token
special_tokens = {
    "bos_token": "<bos>",
    "eos_token": "<eos>",
    "additional_special_tokens": ["User 1:", "User 2:", "conversation:"]
}
tokenizer.add_special_tokens(special_tokens)
print("number of tokens: ", len(tokenizer))

class DatasetLabeling(Dataset):
    def __init__(self, dataset, tokenizer):
        self.dataset = dataset
        self.tokenizer = tokenizer

    def __len__(self):
        return len(self.dataset)

    def __getitem__(self, idx):
        text = self.dataset[idx]
        input_text = text
        output_text = text
        input_token = self.tokenizer.encode(input_text)
        output_token = self.tokenizer.encode(output_text)
        input_token = torch.tensor(input_token, dtype=torch.long)[0:-1]
        output_token = torch.tensor(output_token, dtype=torch.long)[1:]
        return input_token.squeeze(0), output_token.squeeze(0)

train_size = int(0.9 * len(total_dataset['data']))
val_size = len(total_dataset['data']) - train_size
def collate_fn(batch):
    inputs, targets = zip(*batch)
    inputs_padded = pad_sequence(inputs, batch_first=True, padding_value=tokenizer.pad_token_id)
    targets_padded = pad_sequence(targets, batch_first=True, padding_value=-100)  # for CrossEntropyLoss ignore_index
    return inputs_padded, targets_padded

data_train, data_validation = random_split(total_dataset['data'], [train_size, val_size])

train_loader = DataLoader(DatasetLabeling(data_train, tokenizer), batch_size= 1, shuffle= True, collate_fn=collate_fn)
validation_loader = DataLoader(DatasetLabeling(data_validation, tokenizer), batch_size= 1, collate_fn=collate_fn)

T1 = fist.Model(vocab_size=len(tokenizer), emd_dim=fist.emd_dim, n_layers=fist.n_layers, n_heads=fist.n_heads, max_seq_len=fist.max_seq_len, dropout=.1)
T1 = T1.to("cuda")
optimizer = Adam(T1.parameters(), lr=0.001)  # Initialize with model params + learning rate loss_function = CrossEntropyLoss()
loss_function = CrossEntropyLoss(ignore_index=-100)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
T1 = T1.to(device)
scaler = GradScaler(init_scale=2.**10)

epochs = 3
current_epoch = 0
for _ in range(epochs):
    T1.train()
    total_train_loss = 0
    total_val_loss = 0
    best_val_loss = float('inf')
    counter = 0
    for input_batch, target_batch in train_loader:
        input_batch = input_batch.to(device)                #
        target_batch = target_batch.to(device)               #
        # print(" input: ", input_batch)
        # print(" Target: ", target_batch)
        # time.sleep(1000)
        with autocast():
            logits = T1(input_batch)
            # logits = torch.LongTensor(logits).unsqueeze(0)
            # target_tensor = torch.LongTensor(target_batch) # flattened input and output tensor from 3d to 2d
            loss = loss_function(logits.view(-1, logits.size(-1)),target_batch.view(-1))
        #learning_rate = .0001
        optimizer.zero_grad()
        scaler.scale(loss).backward()
        scaler.step(optimizer)
        scaler.update()

        if counter % 100 == 0:
            torch.cuda.empty_cache()
            gc.collect()

        counter += 1
        total_train_loss += loss.item()
        del loss,logits,target_batch
    avg_train_loss = total_train_loss / len(train_loader)
    print(f"Epoch {_+1} of 3, Average Training Loss: {avg_train_loss:.4f}")

    T1.eval()
    with torch.no_grad():
        for input_batch, target_batch in validation_loader:
            logits = T1(input_batch)
            # logits = torch.LongTensor(logits).unsqueeze(0)
            # target_tensor = torch.LongTensor(target_batch).unsqueeze(0)  # flattened input and output tensor from 3d to 2d
            val_loss = loss_function(logits.view(-1, logits.size(-1)), target_batch.view(-1))
            total_val_loss += val_loss.item()
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
    average_val_loss = total_val_loss / len(validation_loader)
    print(f"Epoch {_ + 1} of 3, Average Validation Loss: {average_val_loss:.4f}")
    if average_val_loss < best_val_loss:
        best_val_loss = average_val_loss
        torch.save(T1.state_dict(), f"T1_model_{current_epoch+1}.pt")
        print("new best model saved!")


