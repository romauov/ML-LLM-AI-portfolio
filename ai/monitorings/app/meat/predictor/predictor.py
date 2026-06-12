"""
Скрипты для обработки данных сырых мониторингов

@author Sergei Romanov, Nikolay Zhabchikov
"""
from app.meat.predictor.models.classifier_predictor import predict_on_classifier
from app.meat.predictor.models.mapping_predictor import predict_on_mapping
from app.meat.predictor.models.stemming_predictor import predict_on_stemming


def make_predictions(df):
    """предсказание product_type

    Args:
        df (DataFrame): датафрейм мониторинга

    Returns:
        DataFrame: датафрейм мониторинга с предсказаниями
    """
    df_for_classifying = df[['product', 'description']].copy()
    df_for_classifying = predict_on_mapping(df_for_classifying)
    df_for_classifying = predict_on_stemming(df_for_classifying)
    df_for_classifying = predict_on_classifier(df_for_classifying)
    df = df.reset_index(drop=True)
    df['product_type'] = df_for_classifying['product_type']

    return df
