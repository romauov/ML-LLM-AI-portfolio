def load_raw_sql(op, file_path):
    """
    Загружает и выполняет SQL-запросы из файла.
    
    :param op: Объект Operations из Alembic
    :param file_path: Путь к файлу с SQL-запросами
    """
    # Получаем соединение в контексте выполнения миграции
    connection = op.get_bind()
    
    with open(file_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    # Получаем сырое DBAPI соединение
    raw_conn = connection.connection
    cursor = raw_conn.cursor()

    try:
        cursor.execute(sql_content)
        raw_conn.commit()
    except Exception as e:
        raw_conn.rollback()
        raise e
    finally:
        cursor.close()
