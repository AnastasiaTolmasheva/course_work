import sqlite3
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from pyxdameraulevenshtein import damerau_levenshtein_distance


def making_features(table_name):
    """
    Создание базы данных с характеристиками на основе данных из исходной таблицы

    На входе:
    - table_name: имя таблицы с исходными данными
    """
    connection = sqlite3.connect("app_database.db")
    query = f"SELECT user_id, username, email, url, phone, mailing_address, country, date_registered, date_last_login, is_fake FROM {table_name};"
    data = pd.read_sql_query(query, connection)
    connection.close()

    data['date_registered'] = pd.to_datetime(data['date_registered'])
    data['date_last_login'] = pd.to_datetime(data['date_last_login'])

    # Создание признаков
    # 1. time_difference: разница в секундах между датой регистрации и последнего входа в аккаунт
    # 2. symb_in_name: доля небуквенных символов в имени пользователя
    # 3. symb_in_email: доля небуквенных символов в почте пользователя
    # 4. neighbour_above: разница во времени в секундах до ближайшего зарегистрированного аккаунта до текущего
    # 5. neighbour_below: разница во времени в секундах до ближайшего зарегистрированного аккаунта после текущего
    # 6. text_neighbour_above: среднее гармоническое расстояний Дамерау—Левенштейна полей username и email с соседом, созданным до текущего аккаунта
    # 7. text_neighbour_below: среднее гармоническое расстояний Дамерау—Левенштейна полей username и email с соседом, созданным после текущего аккаунта
    data['time_difference'] = (data['date_last_login'] - data['date_registered']).dt.total_seconds()
    data['symb_in_name'] = data['username'].apply(lambda x: sum(not c.isalpha() for c in x) / len(x))
    data['symb_in_email'] = data['email'].apply(lambda x: sum(not c.isalpha()for c in x) / len(x))


    def find_time_neighbours(dates):
        """
        Находит ближайшие по времени регистрации аккаунты для каждой строки

        На входе:
        - dates: колонка с датой регистрации

        На выходе:
        - neighbour_above: разница во времени до ближайшего зарегистрированного аккаунта до текущего
        - neighbour_below: разница во времени до ближайшего зарегистрированного аккаунта после текущего
        - index_above: индекс ближайшего зарегистрированного аккаунта до текущего
        - index_below: индекс ближайшего зарегистрированного аккаунта после текущего
        """
        neighbour_above = []
        neighbour_below = []
        index_above = []
        index_below = []

        for i, date in enumerate(dates):
            time_diffs = dates - date
            above = time_diffs[time_diffs < pd.Timedelta(0)]
            below = time_diffs[time_diffs > pd.Timedelta(0)]

            if not above.empty:
                neighbour_above.append(above.max().total_seconds())
                index_above.append(above.idxmax())
            else:
                neighbour_above.append(np.nan)
                index_above.append(np.nan)

            if not below.empty:
                neighbour_below.append(below.min().total_seconds())
                index_below.append(below.idxmin())
            else:
                neighbour_below.append(np.nan)
                index_below.append(np.nan)

        return neighbour_above, neighbour_below, index_above, index_below
    
    data['neighbour_above'], data['neighbour_below'], data['index_above'], data['index_below'] = find_time_neighbours(data['date_registered'])


    def harmonic_mean(a, b):
        """
        Функция для расчета среднего гармонического

        На вход:
        - a и b: числа

        На выход:
        - Среднее гармоническое двух чисел
        """
        if a + b == 0:
            return 0
        return 2 * (a * b) / (a + b)
    

    def calculate_damerau_levenshtein_distance(indexes, data):
        """
        Функция вычисляет расстояние Дамерау—Левенштейна между текущим и соседними аккаунтами в их текстовых полях,
        а затем подсчитывает среднее гармоническое между ними (username и email).

        На входе:
        - indexes: индексы соседних аккаунтов
        - data: исходные данные

        На выходе:
        - distances: среднее гармоническое расстояний Дамерау—Левенштейна полей username и email
        """
        distances = []
        for i, idx in enumerate(indexes):
            if not pd.isna(idx):
                username_distance = damerau_levenshtein_distance(data.at[i, 'username'], data.at[idx, 'username'])
                email_distance = damerau_levenshtein_distance(data.at[i, 'email'], data.at[idx, 'email'])
                harmonic_distance = harmonic_mean(username_distance, email_distance)
                distances.append(harmonic_distance)
            else:
                distances.append(np.nan)
        return distances

    data['text_neighbour_above'] = calculate_damerau_levenshtein_distance(data['index_above'], data)
    data['text_neighbour_below'] = calculate_damerau_levenshtein_distance(data['index_below'], data)

    # Нормализация признаков по столбцам
    scaler = MinMaxScaler()
    numeric_columns = ['time_difference', 'neighbour_above', 'neighbour_below', 'text_neighbour_above', 'text_neighbour_below']
    data[numeric_columns] = scaler.fit_transform(data[numeric_columns])
    data.fillna(0, inplace=True)

    # Преобразование is_fake к целочисленному типу
    data['is_fake'] = data['is_fake'].astype(int)

    features = data[['user_id', 'symb_in_name', 'symb_in_email', 'time_difference', 'neighbour_above', 'neighbour_below', 'text_neighbour_above', 'text_neighbour_below', 'is_fake']]
    
    # Соединение с новой базой данных и запись таблицы
    new_connection = sqlite3.connect("app_database_features.db")
    features.to_sql(table_name, new_connection, if_exists='replace', index=False)
    new_connection.close()
