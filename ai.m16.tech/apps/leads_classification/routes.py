"""
Веб-сервис клавалификатора лидов на основе BERT и Spacy

@author Dmitry Avzalov, Yaroslav Koltashev
"""
from flask import Flask, jsonify, request, render_template
from leads_classification.spacy_dir.spacy_pipeline import spacy_prediction_pipeline
from leads_classification.bert_dir.bert_pipeline import bert_prediction_pipeline
from leads_classification.preprocessing_functions.preprocess_strings import preprocessing_data_for_predict

from . import blueprint


app = Flask(__name__)

class_dict = {
    'встречное предложение (комплиментарное)': 0,
    'уточнение информации': 1,
    'встречное предложение (некомплиментарное)': 2,
    'запрос прайса': 3,
    'запрос конкретной продукции': 4,
    'спам': 5,
    'не могу опеределить класс': 6
}


@blueprint.route('/predict_leads', methods=['POST'])
def predict():
    """
    Прогнозирование результатов.

    Принимает данные в формате JSON и возвращает прогнозированные результаты в формате JSON.

    :param data: Данные для прогнозирования.
    :type data: dict

    :return: Прогнозированные результаты.
    :rtype: dict
    """
    data = request.get_json()
    text_list = data.get('data')
    model_name = data.get('model')
    if data.get('data'):
        if model_name == 'bert':
            prediction = bert_prediction_pipeline(
                text_list, preprocessing_data_for_predict)
        elif model_name == 'spacy':
            prediction = spacy_prediction_pipeline(
                text_list, preprocessing_data_for_predict)

        res = jsonify(
            {
                'predict': 
            [{'class': class_dict[i], 'class_name': i} for i in prediction]
            }
            )
        return res

    return jsonify({'Ошибка': 'Нет данных'})


@blueprint.route('/leads_classification', methods=['GET', 'POST'])
def index():
    """
    Отображение домашней страницы.

    Если метод запроса является POST, извлекаются текст и модель из формы запроса.
    Затем, если текст существует, используется выбранная модель для прогнозирования результатов.
    Результаты прогнозирования, модель и текст передаются в шаблон 'demo_leads_page.html',
    который отображается пользователю.

    Если метод запроса не является POST, отображается пустая домашняя страница.

    :return: Домашняя страница или страница с результатами прогнозирования.
    :rtype: HTML шаблон
    """
    if request.method == 'POST':
        text = request.form['text']
        model = request.form['option']

        if text:
            if model == 'bert':
                prediction = bert_prediction_pipeline(
                    [text], preprocessing_data_for_predict)
            elif model == 'spacy':
                prediction = spacy_prediction_pipeline(
                    [text], preprocessing_data_for_predict)

            return render_template('demo_leads_page.html', predict=prediction[0], model=model, text=text)

    return render_template('demo_leads_page.html')


if __name__ == '__main__':
    app.run(debug=True)
