"""
Demo routes
"""
from lib.db import create_client_ch
from . import blueprint


@blueprint.route('/demo', methods=['GET'])
def demo():
    """
    return text demo
    """
    client = create_client_ch()

    sql = 'SELECT count(*) FROM userStat;'
    items = client.execute(sql)

    return "userStat count: " + str(items[0][0])
