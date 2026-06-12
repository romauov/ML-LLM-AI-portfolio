"""
Модель сети

@author Sergey Goncharov
"""
import torch
from torch import nn


class NetProductRuBert(nn.Module):
    """
    Модель сети для определения продукции
    """

    def __init__(self, bert_name: str, size_line: int, output_sizes: list, dropout: float):
        """
        :param bert_name: Название модели
        :param size_line: Размер линейного слоя
        :param output_sizes: Размер словаря признаков продукта
        :param dropout: Вероятность обнуления элемента
        """
        super().__init__()

        self.bert = torch.hub.load('huggingface/pytorch-transformers', 'model', bert_name)

        # исключение (Dropout)
        self.dropout = nn.Dropout(dropout)

        # линейные слои для каждого признака
        self.linears = nn.ModuleList([
            nn.Sequential(
                nn.Linear(self.bert.pooler.dense.out_features, size_line),
                nn.Linear(size_line, size),
            ) for size in output_sizes
        ])

    def forward(self, input_data):
        """
        Получение результата моделью
        :param input_data: данные из датасета
        :return: результат работы модели
        """
        with torch.no_grad():
            output = self.bert(input_data)
        output = output.last_hidden_state[:, 0, :]

        outputs = []
        for index, _ in enumerate(self.linears):
            output_liner = self.dropout(output)
            output_liner = self.linears[index](output_liner)
            outputs.append(output_liner)

        return outputs
