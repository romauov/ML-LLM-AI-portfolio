"""
Модель для поиска клиентов для отдела продаж

@author Sergey Goncharov
"""

import pytorch_lightning as pl
import torch
import torchmetrics
from torch import nn


# pylint: disable=R0901, W0221
class LitRecService(pl.LightningModule):
    """
    Модель для поиска клиентов для отдела продаж
    """

    def __init__(self, input_site: int):
        super().__init__()

        self.save_hyperparameters()

        self.layers = nn.Sequential(
            nn.Linear(input_site, 128),
            nn.Dropout(0.2),
            nn.ReLU(),
            nn.Linear(128, 256),
            nn.Dropout(0.2),
            nn.ReLU(),
            nn.Linear(256, 2),
        )

        self.criterion = nn.CrossEntropyLoss()

        # pylint: disable=no-value-for-parameter
        self.train_acc = torchmetrics.Accuracy(multiclass=True, num_classes=2)
        self.valid_acc = torchmetrics.Accuracy(multiclass=True, num_classes=2)
        self.valid_roc = torchmetrics.AUROC(num_classes=2)

    def forward(self, x):
        """
        Работа модели
        """

        return self.layers(x)

    def training_step(self, batch, _batch_idx):
        """
        Обучение модели
        """
        x, Y = batch

        preds = self.forward(x)

        loss = self.criterion(preds, Y.view(-1))

        self.train_acc(preds, Y.view(-1))

        return loss

    def training_epoch_end(self, outputs):
        """
        Логирование эпохи
        """
        self.log('train_acc', self.train_acc.compute(), prog_bar=True)

        self.train_acc.reset()

    def validation_step(self, batch, _batch_idx):
        """
        Логирование этапа проверки
        """
        x, Y = batch

        preds = self.layers(x)

        self.valid_acc(preds, Y.view(-1))
        self.valid_roc(preds, Y.view(-1))

    def validation_epoch_end(self, outputs):
        """
        Логирование эпохи проверки
        """

        self.log('valid_acc', self.valid_acc.compute(), prog_bar=True)
        self.log('valid_roc', self.valid_roc.compute(), prog_bar=True)

        self.valid_acc.reset()

    def configure_optimizers(self):
        """
        Создание оптимизатора
        """
        optimizer = torch.optim.Adam(self.parameters(), lr=1e-3)
        return optimizer
