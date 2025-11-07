import pandas as pd
import torch
from transformers import get_scheduler
from torch.cuda.amp import autocast, GradScaler
from torch.utils.data import random_split
from torch.utils.data import DataLoader,Dataset
from transformer import tokenizer,Transformer,Model
from torch.nn import CrossEntropyLoss
from torch.optim import Adam
from deepspeed.ops.adam import DeepSpeedCPUAdam
import deepspeed
import gc
import time
import os
import random
import numpy as np
SEED = 42
def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    os.environ['PYTHONHASHSEED'] = str(seed)

set_seed(SEED)

data_set1 = pd.DataFrame(pd.read_csv("warp/RL/T1/sft_dataset.csv"))
data_set1['data'] = data_set1
data_set1 = data_set1['data']
data_set1 = pd.DataFrame(data_set1)
data_set2 = pd.DataFrame(pd.read_csv("warp/RL/T1/gen_dataset.csv"))
data_set2['data'] = data_set2
data_set2 = data_set2['data']
data_set2 = pd.DataFrame(data_set2)
data_set3 = pd.DataFrame(pd.read_csv("warp/RL/T1/cleaned_template.csv"))
data_set = pd.DataFrame(pd.concat([data_set1,data_set2],axis=0))
data_set['data'] = pd.DataFrame(pd.concat([data_set1,data_set2],axis=0))
data_set = data_set.reset_index(drop=True)
data_set = data_set
embedding = 1450
num_head = 25
num_layer = 30
dropout = 0.1
max_seq_len = 4000
vocab_size = len(tokenizer)
train_size = int(0.9 * len(data_set['data']))
val_size = len(data_set['data']) - train_size


train_dataset, validation_set = random_split(data_set['data'], [train_size, val_size])
from torch.nn.utils.rnn import pad_sequence


def collate_fn(batch):
    inputs, targets = zip(*batch)
    inputs_padded = pad_sequence(inputs, batch_first=True, padding_value=tokenizer.pad_token_id)
    targets_padded = pad_sequence(targets, batch_first=True, padding_value=-100)
    return inputs_padded, targets_padded

class dataset_labeling(Dataset):
    def __init__(self, data_set, tokenizer):
        self.data_set = pd.DataFrame(data_set[60000:])
        self.data_set = self.data_set.reset_index(drop=True)
        self.tokenizer = tokenizer

    def __len__(self):
        return len(self.data_set)

    def __getitem__(self, index):
        text = str(self.data_set.iloc[index,0])
        input_text = text
        output_text = text

        input_tokens = self.tokenizer.encode(input_text, return_tensors=None)
        target_tokens = self.tokenizer.encode(output_text, return_tensors=None)

        input_ids = torch.tensor(input_tokens, dtype=torch.long).to(device)[0:-1]
        target_ids = torch.tensor(target_tokens, dtype=torch.long).to(device)[1:]

        return input_ids, target_ids


train_loader = DataLoader(dataset_labeling(train_dataset, tokenizer), batch_size=2, shuffle=True,collate_fn=collate_fn)
validation_loader = DataLoader(dataset_labeling(validation_set,tokenizer),batch_size=2,collate_fn=collate_fn)
loss_function = CrossEntropyLoss(ignore_index=-100)
T1 = Model(vocab_size,embedding,num_layer,num_head,max_seq_len,dropout)

T1.load_state_dict(torch.load('warp/RL/T1/T1_model_mid.pth'))
optimizer = DeepSpeedCPUAdam(T1.parameters(),lr = 6e-5)
model_engine, optimizer, _, _ = deepspeed.initialize(
    model=T1,
    optimizer = optimizer,
    config="warp/RL/T1/ds_config.json",
    model_parameters=T1.parameters()
)

epochs =5
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
#T1 = T1.to(device)
model_engine.to(device)
count = 0
#scaler = GradScaler(init_scale=2.**16)
current_epoch = 0
torch.backends.cuda.matmul.allow_tf32 = True
import os
best_val_loss = float("inf") ##########################don't forget to change this to inf
for _ in range(epochs):
    T1.train()
    print(f"\nSTARTING THE EPOCH NUMBER: {current_epoch+1}")
    total_train_loss = 0
    total_val_loss = 0
    avg_train_loss_total =0
    counter_epoch =360001
    for input_batch,target_batch in train_loader:
        
        
        if counter_epoch>535000:
            break
        if len(input_batch[0])>3980:
            count +=1
            counter_epoch+=1
            continue
        count +=1
        input_batch = input_batch.to(device)
        target_batch = target_batch.to(device)
        #with autocast(): 
        logits = model_engine(input_batch)
        #logits_tensor = torch.LongTensor(logits).unsqueeze(0)
        logits_flat = logits.view(-1, logits.size(-1))
        target_flat = target_batch.view(-1)
        loss = loss_function(logits_flat,target_flat)
        #torch.nn.utils.clip_grad_norm_(T1.parameters(), max_norm=1.0)
        #optimizer.zero_grad()
        model_engine.backward(loss)
        model_engine.step()
        total_train_loss += loss.item()
        avg_train_loss_total +=loss.item()
        if count%40==0:

            print(f"\nCurrent Loss (epoch no.{current_epoch+1}):    ",loss)
            
        if count%100==0:
            gc.collect()
            torch.cuda.empty_cache()
            
        if count%400==0:
            current_lr =  model_engine.get_lr()
            print("\ninput_batch:    ",input_batch,"\n")
            print("target_batch",target_batch,'\n')
            print(f"\nat Row: {counter_epoch}, Avg_loss: {avg_train_loss_total/400} with current lr: {current_lr}\n\n\n")
            torch.save(optimizer.state_dict(), 'warp/RL/T1/optimizer_only.pth')
            avg_train_loss_total = 0
                
        if count%60000==0:
            torch.save(T1.state_dict(), f"warp/RL/T1/T1_model_mid.pth")
            print("New best model saved!")
        counter_epoch +=1
        del loss,logits,logits_flat,target_flat
        
    avg_train_loss = total_train_loss / len(train_loader)
    print(f"Epoch {current_epoch+1}/{epochs} and Training Loss: {avg_train_loss:.4f}")
    torch.cuda.empty_cache()
    torch.cuda.ipc_collect()
    T1.eval()
    with torch.no_grad():
        for input_batch,target_batch in validation_loader:
            logits = T1(input_batch)
            #logits_tensor = torch.LongTensor(logits).unsqueeze(0)
            logits_flat = logits.view(-1, logits.size(-1))
            target_flat = target_batch.view(-1)
            val_loss = loss_function(logits_flat,target_flat)
            total_val_loss +=val_loss.item()
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
    avg_val_loss = total_val_loss / len(validation_loader)
    print(f"\n\nEpoch {current_epoch+1}/{epochs} and validation Loss: {avg_val_loss:.4f}")
    if avg_val_loss < best_val_loss:
        best_val_loss = avg_val_loss
        torch.save(T1.state_dict(), f"warp/RL/T1/T1_model_new_lr_{current_epoch+1}.pth")
        print("New best model saved!")
    current_epoch+=1   
        
                
        




