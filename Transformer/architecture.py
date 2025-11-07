import time

from transformers import GPT2TokenizerFast, GPTNeoConfig, GPTNeoForCausalLM, LongformerConfig, LongformerTokenizer, \
    LongformerForSequenceClassification
import torch
import torch.nn as nn
import torch.nn.functional
import csv
from torch.utils.checkpoint import checkpoint

# 500 million parameters
vocab_size = 50257
emd_dim = 1456
n_layers = 20
n_heads = 16
max_seq_len = 4098
dropout = 0.1


class TransformerBlock(nn.Module):
    def __init__(self, emd_dim=1452, n_heads=22, dropout=0.1):
        super().__init__()
        self.emd_dim = emd_dim
        self.n_heads = n_heads
        self.layerNorm1 = nn.LayerNorm(emd_dim)
        self.attentionHead = nn.MultiheadAttention(emd_dim, n_heads, dropout=dropout, batch_first=True)
        self.layerNorm2 = nn.LayerNorm(emd_dim)

        self.mlp = nn.Sequential(
            nn.Linear(emd_dim, 4 * emd_dim),
            nn.GELU(),
            nn.Linear(4 * emd_dim, emd_dim),
            nn.Dropout(dropout),
        )

    def forward(self, x, attn_mask=None):
        # self attention with residual with causal masking
        x_norm = self.layerNorm1(x)
        # if attn_mask is None:
        #     seq_len = x_norm.size(1)
        #     attn_mask = torch.tril(torch.ones(seq_len,seq_len)).bool().to(x.device)
        if attn_mask is None:
            device = x_norm.device
            seq_len = x_norm.size(1)
            attn_mask = torch.tril(torch.ones(seq_len, seq_len, device=device)).float()
            attn_mask = attn_mask.masked_fill(attn_mask == 0, float('-inf'))

        # print(attn_mask)
        attn_output, _ = self.attentionHead(x_norm, x_norm, x_norm,
                                            attn_mask=attn_mask)  # we give 3 times x_norm for self attention k,q,v   '_' = attention weights

        x = x + attn_output

        # feedforward with residual
        x_norm = self.layerNorm2(x)
        mlp_output = self.mlp(x_norm)
        x = x + mlp_output
        return x


class Model(nn.Module):
    def __init__(self, vocab_size, emd_dim, n_layers, n_heads, max_seq_len, dropout=.1):
        super().__init__()
        self.token_embedding = nn.Embedding(vocab_size,
                                            emd_dim)  # 50257,1020 -- it creates a random matrix of that dimension with random weights
        self.position_embedding = nn.Embedding(max_seq_len,
                                               emd_dim)  # 828, 1020  -- it creates a random matrix of that dimension with random weights

        self.blocks = nn.ModuleList([
            TransformerBlock(emd_dim, n_heads, dropout=dropout)
            for _ in range(n_layers)
        ])

        self.layerNormFinal = nn.LayerNorm(emd_dim)
        self.head = nn.Linear(emd_dim, vocab_size, bias=False)  # guess of next token out of all the token

    def forward(self, tokens):
        seq_len = len(tokens)
        # token_tensor = torch.LongTensor(tokens).unsqueeze(0)  # converts it to long tensor
        # token_tensor = torch.tensor(tokens, dtype=torch.long, device=self.token_embedding.weight.device).unsqueeze(0)
        # token_tensor = torch.tensor(tokens, dtype=torch.long, device=self.token_embedding.weight.device)
        if isinstance(tokens, torch.Tensor):
            token_tensor = tokens.to(self.token_embedding.weight.device)
        else:
            token_tensor = torch.tensor(tokens, dtype=torch.long, device=self.token_embedding.weight.device)

        word_vector = self.token_embedding(token_tensor)

        # position_list = [i for i in range(len(token_tensor))]  # positions/indexes of tensor i.e. 0,1,2,3,4,....
        # position_tensor = torch.arange(token_tensor.size(1)).unsqueeze(0)  # [1, seq_len]
        # position_tensor = torch.arange(token_tensor.size(1), device=token_tensor.device).unsqueeze(0)
        position_tensor = torch.arange(token_tensor.size(1), device=token_tensor.device)
        position_vector = self.position_embedding(position_tensor)

        final_embedding = word_vector + position_vector
        print(seq_len)
        for block in self.blocks:
            final_embedding = checkpoint(block, final_embedding, use_reentrant=False)

        final_embedding = self.layerNormFinal(final_embedding)
        logits = self.head(final_embedding)
        return logits


# device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# print(f"Using device: {device}")
#
# model_path = "T1_best_model_epoch_3.pt"  # Example: Assuming epoch 3 was the best
#
# # tokenizer
# tokenizer = LongformerTokenizer.from_pretrained("allenai/longformer-base-4096")
# tokenizer.pad_token = tokenizer.eos_token
# special_tokens = {
#     "bos_token": "<bos>",
#     "eos_token": "<eos>",
#     "additional_special_tokens": ["User 1:", "User 2:", "conversation:"]
# }
# tokenizer.add_special_tokens(special_tokens)
# print("number of tokens: ", len(tokenizer))
#   # to get the token ids
# vocab_size = len(tokenizer)
# T1 = Model(vocab_size, emd_dim, n_layers, n_heads, max_seq_len, dropout=.1)
# # T1.load_state_dict(torch.load(model_path, map_location=device))
# T1.to(device)
# output_str = " "
#
# with torch.no_grad():
#     prompt = input(">>>")
#     decoded_text = " "
#     while True:
#         if decoded_text == "\n" or decoded_text == "<eos>":
#             break
#         else:
#             tokens = tokenizer.encode(prompt)
#             tokens = torch.tensor(tokens).unsqueeze(0)
#             logits = T1(tokens)
#             # print(tokens)
#             # print(logits, "shape: ",logits.shape)
#             predicted_tokens = torch.argmax(logits, dim=-1)[0]  # shape: [seq_len]
#             decoded_text = tokenizer.decode(predicted_tokens[-1].tolist(), skip_special_tokens=True)
#             output_str += decoded_text
#             prompt = f"<bos> conversation: User 1: {output_str} \n User 2: "
#             print("decoded: ", decoded_text)
#
#             tokens = tokenizer.encode(output_str)
#             print("output: ", output_str)
#             time.sleep(.5)
