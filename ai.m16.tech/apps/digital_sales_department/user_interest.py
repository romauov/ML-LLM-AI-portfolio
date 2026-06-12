"""
Робота модели LitRecService

@author Sergey Goncharov
"""

import pytorch_lightning as pl
import torch
from pytorch_lightning.callbacks import ModelCheckpoint
from torch.utils.data import DataLoader

from digital_sales_department.dataset import load_dataset_train, dataset_users
from digital_sales_department.model import LitRecService


def user_interest_prediction(users: list) -> list:
    """
    Определение заинтересованности пользователей в услуги

    :param users: id пользователей
    :return:
    """
    dataset = dataset_users(users)

    data = torch.Tensor(dataset.values)

    model = LitRecService.load_from_checkpoint("apps/digital_sales_department/data/model/model.ckpt")

    model.eval()

    output = model(data)
    output = torch.nn.functional.normalize(output)

    result = []

    for index, item in enumerate(output):
        index_value = item.argmax(dim=0).item()

        result.append({
            "user_id": users[index],
            "value": index_value,
            "probability": item.tolist()
        })

    return result


def train_model():
    """
    Обучение модели
    """
    dataset_train, dataset_val, input_size = load_dataset_train()

    batch_size = 1000

    data_train = DataLoader(dataset_train, batch_size)
    data_val = DataLoader(dataset_val, batch_size)

    model = LitRecService(input_size)

    checkpoint_callback = ModelCheckpoint(
        dirpath="apps/digital_sales_department/data/model",
        filename="model",
        monitor="valid_acc",
        mode='max'
    )

    trainer = pl.Trainer(
        callbacks=[checkpoint_callback],
        max_epochs=150,
        log_every_n_steps=50,
        logger=True,
        accelerator="cuda",
    )

    trainer.fit(
        model=model,
        train_dataloaders=data_train,
        val_dataloaders=data_val,
    )
