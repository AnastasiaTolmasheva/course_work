import numpy as np
import pandas as pd
import os
from sklearn.preprocessing import MinMaxScaler
from pyxdameraulevenshtein import damerau_levenshtein_distance


app_root = os.getcwd()
datasets_dir = os.path.join(app_root, "datasets")
teaching_dir = os.path.join(app_root, "teaching")


def save_data_to_csv(data, table_name, app_root):
    """
    Сохранение данных из базы данных в CSV-файл в папке datasets внутри приложения

    На входе:
    - data: данные для сохранения
    - table_name: имя датасета
    - app_root: путь до корня приложения
    """
    csv_filename = os.path.join(datasets_dir, f"{table_name}.csv")
    data.to_csv(csv_filename, index=False)  # Сохранение данных в CSV


def get_max_user_id(data):
    """
    Функция для получения максимального user_id

    На входе:
    - data: данные для нахождения индекса

    На выходе:
    - max_id: целое число, максимальное значение user_id. Если таблица пустая или отсутствуют значения user_id, возвращается None
    - None: если нет user_id
    """
    user_ids = data["user_id"].astype(int)

    # Если нет пользователей, возвращаем None
    if user_ids.empty:
        return None
    return user_ids.max()


def balance_data(file_name):
    """
    Балансировка данных в таблице до равного количества записей фейковых и настоящих аккаунтов
    
    На входе:
    - table_name: имя таблицы, в которой происходит аугментация

    На выходе:
    - fake_count_before: количество фейков до аугментации
    - real_count_before: количество настоящих аккаунтов до аугментации
    - fake_count_after: количество фейков после аугментации
    - real_count_after: количество настоящих аккаунтов после аугментации
    """
    file_path = os.path.join(app_root, "datasets", file_name)
    data = pd.read_csv(file_path)

    # Подсчет количества записей фейковых и настоящих аккаунтов
    fake_count_before = data[data["is_fake"] == 1].shape[0]
    real_count_before = data[data["is_fake"] == 0].shape[0]
    
    # Если фейков больше настоящих аккаунтов, то увеличиваем количество настоящих
    if fake_count_before > real_count_before:
        data_to_augment = data[data["is_fake"] == 0]
        num_rows_to_create = fake_count_before - real_count_before  # Определяем сколько новых настоящих записей нужно создать

    # Если настоящих аккаунтов больше фейков, то увеличиваем количество фейков
    elif real_count_before > fake_count_before:
        data_to_augment = data[data["is_fake"] == 1]
        num_rows_to_create = real_count_before - fake_count_before  # Определяем сколько новых фейковых записей нужно создать

    # Иначе аугментация не требуется
    else:
        fake_count_after = fake_count_before
        real_count_after = real_count_before
        print("Аугментацияя не требуется")
        print(f"Фейки до: {fake_count_before}\n", f"Настоящие аккаунты до: {real_count_before}\n", f"Фейки после: {fake_count_after}\n", f"Настоящие аккаунты после: {real_count_after}\n")
        return fake_count_before, real_count_before, fake_count_after, real_count_after
    
    # Получение максимального значение user_id, чтоб вставлять записи после него
    max_user_id = get_max_user_id(data)
    
    augmented_data = []
    for _ in range(num_rows_to_create):
        new_user_id = int(max_user_id) + 1
        new_row_values = [new_user_id] + [np.random.choice(data_to_augment[col].values) for col in data.columns[1:]]
        augmented_data.append(new_row_values)
        max_user_id +=1

    # Добавление новых записей к оригинальным данным
    augmented_data_df = pd.DataFrame(augmented_data, columns=data.columns)
    final_data = pd.concat([data, augmented_data_df], ignore_index=True)
    
    # Сохранение новых данных в CSV-файл
    table_name = f"dataset_augment"
    save_data_to_csv(final_data, table_name, app_root)

    # Определение по индексу is_fake, какие данные были аугментированы (фейковые или настоящие)
    is_fake_in_augmented = augmented_data_df["is_fake"].iloc[1]
    
    # Определяем количество аккаунтов после аугментации
    if is_fake_in_augmented == 1:
        fake_count_after = fake_count_before + num_rows_to_create
        real_count_after = real_count_before
    else:
        real_count_after = real_count_before + num_rows_to_create
        fake_count_after = fake_count_before

    print(f"Фейки до: {fake_count_before}\n", f"Настоящие аккаунты до: {real_count_before}\n", f"Фейки после: {fake_count_after}\n", f"Настоящие аккаунты после: {real_count_after}\n")
    return fake_count_before, real_count_before, fake_count_after, real_count_after


def making_features(file_name):
    """
    Создание базы данных с характеристиками на основе данных из исходной таблицы

    На входе:
    - file_name: имя файла с исходными данными
    """
    file_path = os.path.join(app_root, "datasets", file_name)
    data = pd.read_csv(file_path)

    # Преобразование даты в datetime
    data['date_registered'] = pd.to_datetime(data['date_registered'])
    data['date_last_login'] = pd.to_datetime(data['date_last_login'])

    # Создание признаков
    # 1. time_difference: разница в секундах между датой регистрации и последнего входа в аккаунт
    # 2. symb_in_name: доля небуквенных символов в имени пользователя
    # 3. symb_in_email: доля небуквенных символов в почте пользователя
    # 4. neighbour_above: разница во времени в секундах до ближайшего зарегистрированного аккаунта до текущего
    # 5. neighbour_below: разница во времени в секундах до ближайшего зарегистрированного аккаунта после текущего
    # 6. text_neighbour_above: гармоническое среднее расстояний Дамерау—Левенштейна полей username и email с соседом, созданным до текущего аккаунта
    # 7. text_neighbour_below: гармоническое среднее расстояний Дамерау—Левенштейна полей username и email с соседом, созданным после текущего аккаунта
    data['time_difference'] = (data['date_last_login'] - data['date_registered']).dt.total_seconds()
    data['symb_in_name'] = data['username'].apply(lambda x: sum(not c.isalpha() for c in x) / len(x))
    data['symb_in_email'] = data['email'].apply(lambda x: sum(not c.isalpha()for c in x) / len(x))

    # Функция для нахождения ближайших зарегистрированных аккаунтов
    def find_time_neighbours(dates):
        """
        Находит ближайшие по времени регистрации аккаунты для каждой строки

        На входе:
        - dates: Series с датами регистрации

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
        if a + b == 0:
            return 0
        return 2 * (a * b) / (a + b)
    

    def calculate_damerau_levenshtein_distance(indexes, data):
        """
        Вычисляет расстояние Дамерау—Левенштейна между текущим аккаунтом и соседними аккаунтами,
        затем вычисляет среднее гармоническое для каждого аккаунта.

        На входе:
        - indexes: индексы соседних аккаунтов
        - data: датафрейм с данными

        На выходе:
        - harmonic_distances: гармоническое среднее расстояний Дамерау—Левенштейна
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

    # Применение функции к данным
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
    
    table_name = file_name[:-4] + "_features"
    save_data_to_csv(features, table_name, app_root)
