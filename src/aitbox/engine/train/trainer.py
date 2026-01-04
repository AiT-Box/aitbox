#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File        : trainer.py
Project     : aitbox
Author      : gdd
Created     : 2026-01-02
Description :
"""

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import torch

from aitbox.engine.train.base import StepOutput, TrainModelBase
from aitbox.engine.train.callbacks.base import CallbackMixin
from aitbox.engine.train.callbacks.wrapper import InfiniteLoader, ddp_master_only


@dataclass
class BatchResultData:
    """ """

    batch_idx: int = 0
    batch: Any = None
    batch_result: Any = None
    batch_loss: Any = 0

    def set_batch(self, batch_idx: int, batch: Any):
        """ """
        self.batch = batch
        self.batch_idx = batch_idx

    def set_batch_output(self, output: StepOutput):
        """ """
        self.batch_loss = output.loss
        self.batch_result = output.prediction


@dataclass
class ResultData:
    """ """

    loader: Any = None
    prediction: list = field(default_factory=list)
    total_loss: Any = 0
    prediction_saved: bool = False

    acc_batch_idx: int = 0
    train_loss_list: list = field(default_factory=list)
    val_loss_list: list = field(default_factory=list)
    test_loss_list: list = field(default_factory=list)

    def init(self, loader):
        """ """
        self.loader = loader
        self.prediction.clear()
        self.total_loss = 0

    def set_acc_batch_idx(self):
        """ """
        self.acc_batch_idx += 1

    def append(self, output: StepOutput):
        """ """
        self.total_loss += output.loss.item() / len(self.loader)
        if self.prediction_saved:
            self.prediction.append(output.prediction)

    def final(self, name):
        """ """
        getattr(self, f"{name}_loss_list").append(self.total_loss)


@dataclass
class LoaderInfo:
    """ """

    loader: Any = None
    num_batches_per_epoch: int = 0
    
    def set_info(self, loader, num_batches_per_epoch):
        """ """
        self.loader = loader
        self.num_batches_per_epoch = num_batches_per_epoch

    @property
    def max_batches(self):
        """ """
        return self.num_batches_per_epoch or len(self.loader)


class Trainer(CallbackMixin):
    """ """

    def __init__(
        self,
        model: TrainModelBase,
        device=None,
        epochs=None,
        callbacks=None,
    ):
        """ """
        super().__init__()
        self.model = model
        self.device = device
        self.epochs = epochs
        self.init_callbacks(callbacks)

        self.grad_accumulate_step = 1
        self.fit_stop_signal = False
        self.epoch = 0

        self.train_loader_info = LoaderInfo()
        self.val_loader_info = LoaderInfo()
        self.test_loader_info = LoaderInfo()

        self.result_data = ResultData()
        self.batch_result_data = BatchResultData()
        self.optimizer, self.scheduler = None, None

    def fit(
        self,
        train_loader,
        val_loader,
        test_loader=None,
        epochs=None,
        device=None,
        val_interval=1,
        test_interval=1,
        num_batches_per_epoch=None,
        grad_accumulate_step=1,
        val_num_batches_per_epoch=None,
        test_num_batches_per_epoch=None,
    ):
        """ """
        self("initialize")
        self.set_attr("epochs", epochs)
        self.set_attr("device", device)
        self.set_attr("grad_accumulate_step", grad_accumulate_step)
        self.set_loader_info(
            [num_batches_per_epoch, val_num_batches_per_epoch, test_num_batches_per_epoch],
            [train_loader, val_loader, test_loader],
        )
        self.set_model()
        self("configure_optimizer")
        self("before_fit")
        for epoch in range(1, self.epochs + 1):
            self.epoch = epoch
            self("before_epoch")
            self.train_epoch()
            if self.val_loader_info.loader is not None and epoch % val_interval == 0:
                self.validate()
            if self.test_loader_info.loader is not None and epoch % test_interval == 0:
                self.test()
            if self.fit_stop_signal:
                break
            self("after_epoch")
        self("after_fit")
        if self.test_loader_info.loader is not None:
            self.test()
        self("finalize")

    def train_epoch(self):
        """ """
        self.model.train()
        self.result_data.init(self.train_loader_info.loader)
        self("before_epoch_train")
        for batch_idx in range(1, self.train_loader_info.max_batches + 1):
            batch = next(self.train_loader_info.loader)
            self("before_batch_train")
            batch = self.set_data(batch)
            self.result_data.set_acc_batch_idx()
            self.batch_result_data.set_batch(batch_idx, batch)
            output: StepOutput = self.model.train_step(batch)
            self("after_batch_train_step")
            self.batch_result_data.set_batch_output(output)
            self.result_data.append(output)
            if output.loss.isnan().items():
                raise ValueError(f"Epoch:{self.epoch} Batch:{batch_idx} train loss is nan!")
            self("backward")
            self("optimizer")
            self("after_batch_train")
        self.result_data.final("train")
        self("after_epoch_train")

    @torch.no_grad()
    def validate(self):
        """"""
        self.model.eval()
        self.result_data.init(self.val_loader_info.loader)
        self("before_validate")
        for batch_idx in range(1, self.val_loader_info.max_batches + 1):
            batch = next(self.val_loader_info.loader)
            self("before_batch_validate")
            batch = self.set_data(batch)
            self.batch_result_data.set_batch(batch_idx, batch)
            output: StepOutput = self.model.validate_step(batch)
            self.batch_result_data.set_batch_output(output)
            self.result_data.append(output)
            self("after_batch_validate")
        self.result_data.final("val")
        self("after_validate")

    @torch.no_grad()
    def test(self):
        """"""
        self.model.eval()
        self.result_data.init(self.test_loader_info.loader)
        self("before_test")
        for batch_idx in range(1, self.test_loader_info.max_batches + 1):
            batch = next(self.test_loader_info.loader)
            self("before_batch_test")
            batch = self.set_data(batch)
            self.batch_result_data.set_batch(batch_idx, batch)
            output: StepOutput = self.model.test_step(batch)
            self.batch_result_data.set_batch_output(output)
            self.result_data.append(output)
            self("after_batch_test")
        self.result_data.final("test")
        self("after_test")

    def set_attr(self, name, value):
        """ """
        if value is not None:
            setattr(self, name, value)

    def set_loader_info(self, num_batches_per_epoch_list, loader_list):
        """ """
        for name, loader, num_batches_per_epoch in zip(
            ["train", "val", "test"], loader_list, num_batches_per_epoch_list
        ):
            loader = InfiniteLoader(loader)
            getattr(self, f"{name}_loader_info").set_info(loader, num_batches_per_epoch)

    def set_model(self):
        """ """
        if self.device is not None:
            self.model.to(self.device)

    def set_data(self, data):
        """ """
        if self.device is None:
            return data
        if isinstance(data, torch.Tensor):
            return data.to(self.device)
        elif isinstance(data, list):
            return [self.set_data(d) for d in data]
        elif isinstance(data, tuple):
            return tuple([self.set_data(d) for d in data])
        elif isinstance(data, dict):
            return {k: self.set_data(v) for k, v in data.items()}
        elif isinstance(data, np.ndarray):
            return self.set_data(torch.from_numpy(data))
        else:
            return data

    @ddp_master_only
    def save_model(self, save_path):
        """ """
        return self.model.save_model(save_path)
