import sqlite3
import pandas as pd
import re
import Levenshtein
import numpy as np

# Паттерн для проверки email по шаблону "user@domain.com"
pattern = r'^\S+@\S+\.\S+$'
# Порог сходства (расстояние Левенштейна) для сравнения имен пользователей и имени в email
threshold = 6
# Порог сходства для email
email_similarity = 6


def create_features_database(table_name):
    """
    Создание базы данных с характеристиками на основе данных из исходной таблицы

    На входе:
    - table_name: имя таблицы с исходными данными
    """
    # Соединение с исходной базой данных
    connection = sqlite3.connect('app_database.db')

    # Чтение данных из исходной таблицы
    query = f"SELECT * FROM {table_name};"
    data = pd.read_sql_query(query, connection)
    connection.close()

    # Вычисление необходимых характеристик
    # username_length - длина имени пользователя
    # numbers_in_name - наличие чисел в имени пользователя (ставится 1 при наличии или 0 при отсутствии)
    # email_length - длина email
    # matching_names - проверка, сходятся ли username и email по порогу сходства, установленному раннее (1 - сходятся, 0 - не сходятся)
    # pattern_email - проверка email по установленному раннее шаблону
    # country - проверка, указана ли страна (1 - указана, 0 - не указана)
    # date_last_email - дата последнего отправленного email, если дата есть - 1, если нет - 0
    # date_registered - дата регистрации, преобразованная в формат целых чисел типа int64
    # date_last_login - дата последнего входа, преобразованная в формат целых чисел типа int64
    # matching_dates - сравниваются даты регистрации и последнего входа. Если они совпадают - ставится 1, иначе - 0
    # is_fake - размеченная колонка, содержащая 1 или 0 (1 - аккаунт фейк, 0 - настоящий)

    data['username_length'] = data['username'].str.len()
    data['numbers_in_name'] = data['username'].str.contains(r'\d').astype(int)
    data['email_length'] = data['email'].str.len()
    data['matching_names'] = data.apply(lambda row: int(Levenshtein.distance(row['username'], row['email'].split('@')[0]) <= threshold) if row['email'] is not None else 0, axis=1)
    data['pattern_email'] = data['email'].apply(lambda email: int(bool(re.match(pattern, email))) if email else 0)
    data['country'] = data['country'].notnull().astype(int)
    data['date_last_email'] = data['date_last_email'].replace('NULL', np.nan).notnull().astype(int)
    data['date_registered'] = pd.to_datetime(data['date_registered']).astype('int64')
    data['date_last_login'] = pd.to_datetime(data['date_last_login']).astype('int64')
    data['matching_dates'] = (pd.to_datetime(data['date_last_login']).dt.round('s') == pd.to_datetime(data['date_registered']).dt.round('s'))
    data['matching_dates'] = data['matching_dates'].astype(int)
    data['is_fake'] = data['is_fake'].astype(int)


    def find_neighbours(column_name, radius):
        """
        Находит соседей в радиусе для каждой строки по определенному столбцу

        На входе:
        - column_name: название столбца для поиска соседей
        - radius: радиус поиска

        На выходе:
        - neighbours_above: список соседей сверху
        - neighbours_below: список соседей снизу
        """
        neighbours_above = []
        neighbours_below = []

        for i, value in enumerate(data[column_name]):
            # Поиск соседей снизу от текущей строки
            found_neighbour_below = False
            for j in range(i + 1, min(i + radius + 1, len(data))):
                neighbour_value = data.at[j, column_name]
                if value is not None and neighbour_value is not None and Levenshtein.distance(value, neighbour_value) <= threshold:
                    neighbours_below.append(j - i)  # записываем расстояние в строках
                    found_neighbour_below = True
                    break  # прекращаем поиск после нахождения первого соседа в радиусе
            if not found_neighbour_below:
                neighbours_below.append(None)  # None, если соседей не найдено

            # Поиск соседей сверху от текущей строки
            found_neighbour_above = False
            for j in range(i - 1, max(i - radius - 1, -1), -1):
                neighbour_value = data.at[j, column_name]
                if value is not None and neighbour_value is not None and Levenshtein.distance(value, neighbour_value) <= threshold:
                    neighbours_above.append(i - j)  # записываем расстояние в строках
                    found_neighbour_above = True
                    break  # прекращаем поиск после нахождения первого соседа в радиусе
            if not found_neighbour_above:
                neighbours_above.append(None)  # None, если соседей не найдено
        return neighbours_above, neighbours_below
    
    # Определение радиуса сравнения соседей - это 1/3 датасета
    neighbour_radius = len(data) // 3

    # Добавление столбцов для соседей с похожим username и email
    (data['username_neighbour_above'], data['username_neighbour_below']) = find_neighbours('username', neighbour_radius)
    (data['email_neighbour_above'], data['email_neighbour_below']) = find_neighbours('email', neighbour_radius)

    # Соединение с новой базой данных
    new_connection = sqlite3.connect('app_database_features.db')

    # Создание таблицы с вычесленными признаками
    create_features_table_query = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        user_id INTEGER,
        username_length INTEGER,
        numbers_in_name INTEGER,
        email_length INTEGER,
        matching_names INTEGER,
        pattern_email INTEGER,
        country INTEGER,
        date_last_email INTEGER,
        date_registered INTEGER, 
        date_last_login INTEGER,
        matching_dates INTEGER,
        username_neighbour_above INTEGER,
        username_neighbour_below INTEGER,
        email_neighbour_above INTEGER,
        email_neighbour_below INTEGER,
        is_fake INTEGER
    );
    """
    new_connection.execute(create_features_table_query)

    # Запись вычисленных характеристик в таблицу
    data[['user_id', 'username_length', 'numbers_in_name', 'email_length', 'matching_names',
          'pattern_email', 'country', 'date_last_email', 'date_registered', 'date_last_login', 'matching_dates',
          'username_neighbour_above', 'username_neighbour_below', 'email_neighbour_above', 'email_neighbour_below', 'is_fake']].to_sql(f'{table_name}', new_connection, if_exists='replace', index=False)

    # Прекращение соединения с новой базой данных
    new_connection.close()
