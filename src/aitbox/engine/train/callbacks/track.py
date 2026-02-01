#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File        : track.py
Project     : aitbox
Author      : gdd
Created     : 2026-01-11
Description :
"""

from typing import TYPE_CHECKING

from tqdm import tqdm

from aitbox.engine.train.callbacks.base import Callback
from aitbox.engine.train.callbacks.wrapper import ddp_master_only, tqdm_log_wrapper
from aitbox.utils.log import Log

if TYPE_CHECKING:
    from aitbox.engine.train.trainer import Trainer


class BaseTrackCallback(Callback):
    """ """
    caller: "Trainer"

    
class TqdmTrack(BaseTrackCallback):
    """ """

    def __init__(self, ncols: int = 120):
        """ """
        super().__init__()
        self.ncols = ncols
        self._tqdm: tqdm | None = None
        tqdm_log_wrapper(Log)

    def set_description(self, desc: str):
        """ """
        self._tqdm.set_description(f"{desc} Epoch {self.caller.epoch} / {self.caller.epochs}")
    
    @ddp_master_only
    def before_epoch_train(self):
        """ """
        self._tqdm = tqdm(total=self.caller.train_loader_info.max_batches, ncols=self.ncols)
        self.set_description("Training")

    @ddp_master_only
    def after_batch_train(self):
        """ """
        self._tqdm.set_postfix(total_loss=f"{self.caller.result_data.total_loss:.6f}")
        self._tqdm.update(1)

    @ddp_master_only
    def after_epoch_train(self):
        """ """
        self._tqdm.close()

    @ddp_master_only
    def before_validate(self):
        """ """
        self._tqdm = tqdm(total=self.caller.val_loader_info.max_batches, ncols=self.ncols)
        self.set_description("Valiate")

    @ddp_master_only
    def after_batch_validate(self):
        """ """
        self.after_batch_train()

    @ddp_master_only
    def after_validate(self):
        """ """
        self.after_epoch_train()
        
    @ddp_master_only
    def before_test(self):
        """ """
        self._tqdm = tqdm(total=self.caller.test_loader_info.max_batches, ncols=self.ncols)
        self.set_description("Testing")

    @ddp_master_only
    def after_batch_test(self):
        """ """
        self.after_batch_validate()

    @ddp_master_only
    def after_test(self):
        """ """
        self.after_validate()
