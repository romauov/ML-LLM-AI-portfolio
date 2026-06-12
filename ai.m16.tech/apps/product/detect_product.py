"""
Определение продукции

@author Sergey Goncharov
"""
import torch

from product.dataset import load_tokenizer, text_to_tensor

# список признаков продуктов
targets = ['mtype', 'part', 'ice_status', 'gost', 'ty']

DIR_DATA = 'apps/product/data'


class DetectProductRuBERT:
    """
    Определение продукции
    """
    def __init__(self, bert_name: str, max_length: int) -> None:
        self.max_length = max_length

        # загрузка словарей для текста и признаков продуктов
        self.tokenizer, self.tokenizer_targets = load_tokenizer(bert_name)
        self.model = None
        self.bert_name = bert_name

    def load(self):
        """
        Загрузка модели
        """
        path = DIR_DATA + '/model/' + self.bert_name + '/model-product'

        # загрузка параметров модели из файла
        self.model = torch.load(path, map_location=torch.device('cpu')).cpu()
        # режим тестирования модели
        self.model.eval()

    def detect(self, text: str):
        """
        Определение продукции
        """
        if self.model is None:
            raise RuntimeError("Модель не загружена")

        # преобразование строки в тензор
        x = text_to_tensor(text, self.tokenizer, self.max_length)

        x = x.view(1, x.shape[0])

        # вызов модели
        outputs = self.model(x)

        result = {}

        for index_output, output in enumerate(outputs):
            # нормализация
            output = torch.nn.functional.normalize(output)

            # индекс признака продукта
            index = output.argmax(dim=1).item()

            # вероятность признака продукта
            proba = round(output[0][index].item(), 4)

            # значение признака продукта
            value = self.tokenizer_targets[index_output].get_word(index)
            result[targets[index_output]] = {
                'proba': proba,
                'value': value,
            }

        return result
