import math

from torch import nn
import torch.nn.functional as F

"""
缩放点积注意力机制 - 测试版
Author: wukunrun
Date: 2026-01-12
"""


class ScaleDotAttention(nn.Module):

    def __init__(self, in_feature=4, dk=128, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.dk = dk
        self.wq = nn.Linear(in_features=in_feature, out_features=self.dk)
        self.wk = nn.Linear(in_features=in_feature, out_features=self.dk)
        self.wv = nn.Linear(in_features=in_feature, out_features=self.dk)

    def forward(self, x):
        if len(x.shape == 3):
            b, n, d = x.shape
        else:
            n, d = x.shape
        Q = self.wq(x)
        K = self.wk(x)
        V = self.wv(x)
        attn_score = Q @ K.transpose(-2, -1)
        attn_score /= math.sqrt(self.dk)
        attn_score = F.softmax(attn_score, dim=-1)
        output = attn_score @ V
        return output
