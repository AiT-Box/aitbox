#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File        : test_trainer.py
Project     : aitbox
Author      : gdd
Created     : 2026-01-10
Description :
"""

import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader

from aitbox.engine.train.base import StepOutput, TrainModelBase
from aitbox.engine.train.callbacks.track import TqdmTrack
from aitbox.engine.train.trainer import Trainer


class Model(nn.Module):
    """ """

    def __init__(self, in_dim, hidden_dim, out_dim):
        """ """
        super().__init__()
        self.layer = nn.Sequential(
            nn.Linear(in_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, out_dim),
        )

    def forward(self, x):
        """ """
        return self.layer(x)


class TrainModel(TrainModelBase):
    """ """

    def __init__(self, model):
        super().__init__(model)

    def train_step(self, batch):
        x, y = batch
        prediction = self.model(x)
        loss = self.compute_loss(prediction, y)
        return StepOutput(loss, prediction)

    def validate_step(self, batch):
        return self.train_step(batch)

    def test_step(self, batch):
        return self.validate_step(batch)

    def configure_criterion(self):
        return nn.MSELoss()

    def configure_optimizer(self):
        return torch.optim.Adam(self.model.parameters(), lr=1e-3)

    def compute_loss(self, prediction, ground_truth, *args, **kwargs):
        return self.criterion(prediction, ground_truth)


def test_trainer():
    """ """
    x = torch.randn(32, 10)
    y = torch.randn(32, 1)
    dataset = TensorDataset(x, y)
    dataloader = DataLoader(dataset, batch_size=32)
    model = Model(in_dim=10, hidden_dim=32, out_dim=1)
    train_model = TrainModel(model)
    trainer = Trainer(
        model=train_model,
        device=torch.device("cpu"),
        callbacks=[TqdmTrack()]
    )
    trainer.fit(
        train_loader=dataloader,
        epochs=10,
    )


if __name__ == "__main__":
    test_trainer()
