"""
Квалификатор на основе Spacy

@author Dmitry Avzalov, Yaroslav Koltashev
"""
import random

import numpy as np
import spacy # pylint: disable=import-error
# pylint: disable=no-name-in-module
from spacy.training.example import Example # pylint: disable=import-error
import matplotlib.pyplot as plt
from sklearn.metrics import auc, roc_auc_score, precision_recall_curve


class TextClassifer:
    """
    Квалификатор лидов на основе Spacy
    """

    def __init__(self, models_path=None, label_list=None, show_info=True):
        """
        Инициализирует объект класса.

        Аргументы:
            models_path (str, опционально): Путь до модели. По умолчанию None.

            label_list (список, опционально): Список меток классов. По умолчанию None.
            show_info (bool, опционально): Флаг для отображения информации. По умолчанию True.

        Возвращает:
            None
        """
        if models_path:
            self.nlp = spacy.load(models_path)
        else:
            self.nlp = spacy.blank('xx')
            self.nlp.add_pipe('tok2vec')
            self.nlp.add_pipe('textcat')

            self.textcat = self.nlp.get_pipe('textcat')
            self.label_list = label_list

            if label_list:
                for label in label_list:
                    self.textcat.add_label(label)
            else:
                print('''
                Ошибка !!!
                Нужен список классов
                ''')

        if show_info:
            print(f'Pipline: {self.nlp.pipe_names}')
            print(self.nlp.analyze_pipes(pretty=True))

    def fit(self, epoch=10, data_train=None, batch_size=4, val=None):
        """
        Подгоняет модель под тренировочные данные.

        Аргументы:
            epoch (int, опционально): Количество эпох тренировки. По умолчанию 10.
            data_train (list, опционально): Тренировочные данные. По умолчанию None.
            batch_size (int, опционально): Размер пакета для тренировки. По умолчанию 4.
            val (list, опционально): Валидационные данные. По умолчанию None.

        Возвращает:
            None
        """
        optimizer = self.nlp.begin_training()

        best_metrics = 0

        # other_pipes = [pipe for pipe in self.nlp.pipe_names if pipe != 'textcat']
        with self.nlp.disable_pipes([]):  # *other_pipes
            for _ in range(1, epoch + 1):
                random.shuffle(data_train)
                losses = {}
                for batch in spacy.util.minibatch(data_train, size=batch_size):
                    examples = []

                    for text, annotations in batch:
                        doc = self.nlp.make_doc(text)
                        example = Example.from_dict(doc, annotations)
                        examples.append(example)

                    self.nlp.update(examples, sgd=optimizer,
                                    losses=losses, drop=0.2)

                if val:

                    metric = self.evaluate(val)
                    if best_metrics < metric['roc_auc']:
                        best_metrics = metric['roc_auc']
                        self.nlp.to_disk('best_model')

                    print(metric)
                    print('Losses', losses)
                else:
                    print('Losses', losses)

        self.nlp = spacy.load("/kaggle/working/best_model")

    def predict(self, data):
        """
        Прогнозирование результатов.

        Принимает данные для прогнозирования и выполняет прогнозирование с использованием модели Spacy.
        Каждый элемент данных обрабатывается с помощью модели Spacy для получения класса прогноза.
        Класс прогноза добавляется в список прогнозов.

        :param data: Данные для прогнозирования.
        :type data: list

        :return: Прогнозированные результаты.
        :rtype: list
        """
        predict = []

        for elem in data:  # Пробегаемся по каждому элементу
            doc = self.nlp(elem)  # Обрабатываем текст
            pred = max(doc.cats, key=doc.cats.get)  # Класс
            predict.append(pred.lower())

        return predict

    def predict_proba(self, data):
        """
        Выполняет предсказание вероятностей принадлежности классам.

        Аргументы:
            data (list): Входные данные для предсказания.

        Возвращает:
            list: Список вероятностей принадлежности классам.
        """
        predict_proba = []

        for elem in data:  # Пробегаемся по каждому элементу
            doc = self.nlp(elem[0])  # Обрабатываем текст

            arr_predict_proba = []
            for _, lbl in enumerate(self.label_list):
                arr_predict_proba.append(doc.cats[lbl])

            # Исправляем ошибку где сумма значений больше 1 или меньше 1
            try:
                sum_lst = sum(arr_predict_proba)
                new_lst = [el / sum_lst for el in arr_predict_proba]
                predict_proba.append(np.array(new_lst))
            # pylint: disable=bare-except
            except:
                print(f'Входная строка <{elem[0]}>')
                print(f'Ошибка со значениями {doc.cats}')
                print(f'Предсказания:  {arr_predict_proba}')

        return np.array(predict_proba)

    def pr_auc_score(self, data):
        """
        Вычисляет значение PR-AUC метрики для каждого класса.

        Аргументы:
            data (list): Входные данные для вычисления метрики.

        Возвращает:
            None
        """
        y_true = []

        for elem in data:  # Пробегаемся по каждому элементу
            # doc = self.nlp(elem[0])  # Обрабатываем текст
            # print(doc.cats)
            # pred = max(doc.cats, key=doc.cats.get)  # Класс !
            true = list(elem[1].get('cats').keys())[0]  # Класс

            for i, lbl in enumerate(self.label_list):
                if true == lbl:
                    y_true.append([0 for _ in range(i)] + [1] +
                                  [0 for _ in range(len(self.label_list) - i - 1)])
                    break

        y_true = np.array(y_true)
        pr_proba = self.predict_proba(data)

        precision = {}
        recall = {}
        pr_auc = {}
        for i, lbl in enumerate(self.label_list):
            precision[i], recall[i], _ = precision_recall_curve(
                y_true[:, i], pr_proba[:, i])
            pr_auc[lbl] = auc(recall[i], precision[i])

        # Построение кривой Precision-Recall AUC для каждого класса
        plt.figure()
        # plt.plot(recall["micro"], precision["micro"], label='micro-average (AUC = {0:0.2f})'.format(pr_auc["micro"]))
        for i, lbl in enumerate(self.label_list):
            plt.plot(recall[i], precision[i],
                     label=f'class {i} (AUC = {round(pr_auc[lbl], 3)})')
            print(f'PR-AUC class {lbl} ({i}): ', pr_auc[lbl])

        # Настройка внешнего вида графика
        plt.xlabel('Recall')
        plt.ylabel('Precision')
        plt.ylim([0.0, 1.05])
        plt.xlim([0.0, 1.0])
        plt.title('Precision-Recall AUC')
        plt.legend(loc="lower right")
        plt.figure(figsize=(20, 15))
        plt.show()

    def evaluate(self, data):
        """
        Выполняет оценку модели на основе заданных данных.

        Аргументы:
            data (list): Список кортежей в формате text_cat spacy.

        Возвращает:
            dict: Словарь с метриками оценки модели, включая точность (Accuracy) и ROC-AUC (roc_auc).
        """
        count = len(data)
        count_true = 0

        true_labels = []

        # ('порт прибытия спб пкт спб пкт спб пкт', {'cats': {'POSITIVE': 1}}),

        for elem in data:  # Пробегаемся по каждому элементу
            doc = self.nlp(elem[0])  # Обрабатываем текст

            pred = max(doc.cats, key=doc.cats.get)  # Класс
            true = list(elem[1].get('cats').keys())[0]  # Класс

            # arr_predict_proba = []  !
            for i, lbl in enumerate(self.label_list):
                if true == lbl:
                    true_labels.append(i)

            if pred == true:
                count_true += 1

        pr_proba = self.predict_proba(data)

        roc_auc = roc_auc_score(np.array(true_labels),
                                np.array(pr_proba), multi_class='ovr')

        self.pr_auc_score(data)
        return {'Accuracy': count_true / count, 'roc_auc': roc_auc}
