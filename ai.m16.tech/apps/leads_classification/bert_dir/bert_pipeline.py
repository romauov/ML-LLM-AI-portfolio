"""
Pipeline квалификатора лидов с использованием Bert

@author Dmitry Avzalov, Yaroslav Koltashev
"""
from os.path import join
# pylint: disable=import-error
from bert_dir.model_bert import load_and_prepare_bert_model
import torch


class_list = [
    'встречное предложение (комплиментарное)',
    'уточнение информации',
    'встречное предложение (некомплиментарное)',
    'запрос прайса',
    'запрос конкретной продукции'
]


def predict_result(model, data_coded):
    """
    Generates the prediction result using a trained model and coded data.

    Parameters:
        model (torch.nn.Module): The trained model to use for prediction.
        data_coded (List[Dict[int, torch.Tensor]]): The coded data to predict on. 
            Each element in the list is a dictionary containing the input ids and attention mask tensors.

    Returns:
        List[str]: The predicted result as a list of class labels.
    """
    model.eval()
    prediction_result = []
    with torch.no_grad():
        for _, data in enumerate(data_coded):
            input_ids = data["input_ids"]
            attention_mask = data["attention_mask"]
            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask
            )
            pred = torch.argmax(outputs.logits.cpu(), dim=1).numpy()
            for i in pred:
                prediction_result.append(class_list[i].lower())
    return prediction_result


def bert_prediction_pipeline(text_list, preprocessing_data):
    """
    Пайплайн прогнозирования с помощью модели BERT.

    Принимает список текстовых данных и функцию предварительной обработки данных.
    Загружает предварительно обученную модель BERT и применяет ее к предварительно обработанным данным.
    Возвращает прогнозированные результаты.

    :param text_list: Список текстовых данных для прогнозирования.
    :type text_list: list
    :param preprocessing_data: Функция предварительной обработки данных.
    :type preprocessing_data: function

    :return: Прогнозированные результаты.
    :rtype: list
    """
    model, tokenizer = load_and_prepare_bert_model(
        model_path=join('apps', 'leads_classification', 'bert_dir',
                        'model', 'model_bert_messages_5_classes.pth'),
        num_classes=5)

    data_to_predict = preprocessing_data(text_list)
    data_coded = [tokenizer.encode_plus(
        message,
        add_special_tokens=True,
        max_length=512,
        return_token_type_ids=False,
        padding='max_length',
        return_attention_mask=True,
        return_tensors='pt',
    ) for message in data_to_predict]

    prediction = predict_result(model, data_coded)

    return prediction
