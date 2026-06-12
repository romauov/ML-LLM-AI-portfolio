"""
API сервиса для поиска клиентов, взаимодействоваших с кластером продукции

@author Sergei Romanov
"""
import json
from flask import request
from .cluster_rec import predict
from . import blueprint


@blueprint.route('/cluster_recmndr', methods=['POST'])
def get_ids():
    """
    Получение пользователей для рекомендации продукта
    
    input_exapmle = {'type1': "форель", 'type1': "разделка"}
    
    example_out_put = {"user_ids": clients_list}
    """
    query = request.get_json()
    result = predict(**query)
    return json.dumps(result, ensure_ascii=False)
