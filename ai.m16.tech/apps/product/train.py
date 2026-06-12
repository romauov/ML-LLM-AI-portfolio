"""
Обучение сети

команда:
python app/train.py

@author Sergey Goncharov
"""

import statistics
from dataclasses import dataclass
from pathlib import Path

import torch
import torchmetrics
from torch import nn
from torch.utils.data import DataLoader
import mlflow.pytorch

from product.dataset import load_dataset
from product.model import NetProductRuBert
from product.utility import load_params

dev = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")

DIR_DATA = 'apps/product/data'


#
class Metrics:
    """
    Метрика для сети (Accuracy, AUROC)
    """

    def __init__(self, sizes, stat_scores) -> None:
        """
        :param sizes: Количество категорий признаков продукта
        :param stat_scores: Класс метрики statistics
        """
        self.metrics = [stat_scores(task='multiclass', num_classes=size).to(dev) for size in sizes]

    def add(self, outputs, y):
        """
        Добавить прогноз модели и цель
        """
        for index, y_i in enumerate(y):
            self.metrics[index].update(outputs[index], y_i.view(-1))

    def compute(self) -> list:
        """
        Подсчитать метрику и очистить прогнозы модели
        """
        metrics_result = [metric.compute().item() for metric in self.metrics]
        for metric in self.metrics:
            metric.reset()
        return metrics_result


# Обучение модели
def train(model: NetProductRuBert, data_iter: DataLoader, criterion, optimizer, metrics):
    """
    Обучение модели
    """
    loss_sum = 0

    # режим обучения модели
    model.train()
    for X, y_1, y_2, y_3, y_4, y_5 in data_iter:
        # перенос данных на gpu
        X, y_1, y_2, y_3, y_4, y_5 = X.to(dev), y_1.to(dev), y_2.to(dev), y_3.to(dev), y_4.to(dev), y_5.to(dev)

        y = [y_1, y_2, y_3, y_4, y_5]

        # обнуление значения градиента
        optimizer.zero_grad()

        # вызов модели
        outputs = model(X)

        # получение loss
        loss_list = [criterion(outputs[i], yi.view(-1)) for i, yi in enumerate(y)]
        train_loss = sum(loss_list)

        loss_sum += train_loss.item()

        # подсчет градиентов
        train_loss.backward()

        # обновление параметров сети
        optimizer.step()

        # подсчет точности
        metrics.add(outputs, y)

    return loss_sum / len(data_iter), metrics.compute()


def evaluate_accuracy(model: NetProductRuBert, data_iter: DataLoader, metrics_accuracy, metrics_auroc):
    """
    Проверка модели
    """
    # режим тестирования модели
    model.eval()
    for X, y_1, y_2, y_3, y_4, y_5 in data_iter:
        # перенос данных на gpu
        X, y_1, y_2, y_3, y_4, y_5 = X.to(dev), y_1.to(dev), y_2.to(dev), y_3.to(dev), y_4.to(dev), y_5.to(dev)

        y = [y_1, y_2, y_3, y_4, y_5]

        # вызов модели
        outputs = model(X)

        # подсчет точности
        metrics_accuracy.add(outputs, y)
        metrics_auroc.add(outputs, y)

    return metrics_accuracy.compute(), metrics_auroc.compute()


@dataclass
class TrainMetric:
    """
    Метрики обучения модели
    """
    eval_train_acc = []
    eval_train_auroc = []
    eval_test_acc = []
    eval_test_auroc = []

    max_test_auroc = 0
    max_epoch = 0


def train_rubert():
    """
    Обучение модели NetProductRuBert
    """
    path = DIR_DATA + '/ds/meatinfo.csv'

    save_model = True

    params = load_params()

    mlflow.start_run(experiment_id='786681454308179059')
    mlflow.log_param("epoch", params['train']['num_epochs'])
    mlflow.log_param("max_length", params['data']['max_length'])
    mlflow.log_param("bert_name", params['model']['bert_name'])
    mlflow.log_param("dropout", params['model']['dropout'])
    mlflow.log_param("sgd_lr", params['model']['sgd_lr'])
    mlflow.log_param("size_line", params['model']['size_line'])

    # создать директорию для модели
    Path(DIR_DATA + '/model/' + params['model']['bert_name']).mkdir(parents=True, exist_ok=True)

    dataset_train, dataset_val, tokenizer_targets = load_dataset(
        path,
        params['data']['max_length'],
        save_model,
        params['model']['bert_name']
    )

    data_iter_train = DataLoader(dataset_train, params['train']['batch_size'])
    data_iter_val = DataLoader(dataset_val, params['train']['batch_size'])

    output_sizes = [tokenizer.size() for tokenizer in tokenizer_targets]

    model = NetProductRuBert(
        params['model']['bert_name'],
        params['data']['max_length'],
        output_sizes,
        params['model']['dropout']
    ).to(dev)

    # функция перекрёстной энтропии
    criterion = nn.CrossEntropyLoss()

    # оптимизатор стохастический градиентный спуск
    optimizer = torch.optim.SGD(model.parameters(), lr=params['model']['sgd_lr'])

    metrics_accuracy = Metrics(output_sizes, torchmetrics.Accuracy)
    metrics_auroc = Metrics(output_sizes, torchmetrics.AUROC)

    train_metric = TrainMetric()

    for epoch in range(1, params['train']['num_epochs'] + 1):
        _, train_acc = train(model, data_iter_train, criterion, optimizer, metrics_accuracy)
        test_acc, test_auroc = evaluate_accuracy(model, data_iter_val, metrics_accuracy, metrics_auroc)

        train_sum = statistics.mean(train_acc)
        test_sum_acc = statistics.mean(test_acc)
        test_sum_auroc = statistics.mean(test_auroc)

        train_metric.eval_train_acc.append(train_sum)
        train_metric.eval_test_acc.append(test_sum_acc)
        train_metric.eval_test_auroc.append(test_sum_auroc)

        if test_sum_auroc > train_metric.max_test_auroc:
            train_metric.max_epoch = epoch

        train_acc_list = ', '.join([f'{it:.3f}' for it in train_acc])
        test_acc_list = ', '.join([f'{it:.3f}' for it in test_acc])
        test_auroc_list = ', '.join([f'{it:.3f}' for it in test_auroc])

        print(
            f'Epoch {epoch:02d}.'
            f'Train: ({train_sum:.3f}) {train_acc_list},'
            f'Test: ({test_sum_acc:.3f}) {test_acc_list},'
            f'roc: ({test_sum_auroc:.3f}) {test_auroc_list}'
        )

        if epoch > train_metric.max_epoch + 15 or epoch == params['train']['num_epochs']:
            mlflow.log_metric("epoch", epoch)
            mlflow.log_metric("train_acc", round(train_sum, 2))
            mlflow.log_metric("test_acc", round(test_sum_acc, 2))
            mlflow.log_metric("test_auroc", round(test_sum_auroc, 2))
            break

    mlflow.end_run()

    if save_model:
        # сохранение параметров модели в файл
        torch.save(model, DIR_DATA + '/model/' + params['model']['bert_name'] + '/model-product')


if __name__ == '__main__':
    train_rubert()
