import numpy as np
import sqlite3
import pandas as pd
import os


# Используем текущую рабочую директорию как корень приложения
app_root = os.getcwd()


def count_records(database, table_name, condition):
    """
    Подсчет количества записей в таблице базы данных
    
    На входе:
    - database: путь к файлу базы данных
    - table_name: название таблицы
    - condition: условие для фильтрации записей
    
    На выходе:
    - count: количество записей в таблице, удовлетворяющих условию
    """
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    query = f"SELECT COUNT(*) FROM {table_name} WHERE {condition};"
    cursor.execute(query)
    count = cursor.fetchone()[0]
    conn.close()
    return count


def save_augmented_data_to_database(table_name, augmented_data, database):
    """
    Сохранение аугментированных данных в новую таблицу в базе данных
    
    На входе:
    - table_name: название оригинальной таблицы в базе данных
    - augmented_data: аугментированные данные для сохранения
    - database: имя базы данных
    """
    # Получение информации о столбцах оригинальной таблицы
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    
    # Удаление существующей таблицы, если она существует
    cursor.execute(f"DROP TABLE IF EXISTS {table_name}_augment")

    # Получение информации о структуре таблицы
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    column_names = ', '.join([col[1] for col in columns])
    create_table_query = f"CREATE TABLE IF NOT EXISTS {table_name}_augment ({column_names})"
    cursor.execute(create_table_query)
        
    # Вставка изначальных данных в таблицу базы данных
    cursor.execute(f"INSERT INTO {table_name}_augment SELECT * FROM {table_name}")
    
    # Добавление аугментированных данных в конец таблицы
    for row in augmented_data:
        placeholders = ', '.join(['?' for _ in row])
        cursor.execute(f"INSERT INTO {table_name}_augment VALUES ({placeholders})", row)
    
    # Сохранение изменений
    conn.commit()
    conn.close()


# Функция для сохранения данных в CSV
def save_augmented_data_to_csv(database, table_name, app_root):
    """
    Сохранение данных из базы данных в CSV-файл в папке datasets внутри приложения
    """
    conn = sqlite3.connect(database)
    query = f"SELECT * FROM {table_name};"  # Выбираем все данные из таблицы
    data = pd.read_sql_query(query, conn)

    # Определяем путь к папке datasets внутри приложения
    folder_path = os.path.join(app_root, "datasets")
    
    # Создаем папку datasets, если ее еще нет
    os.makedirs(folder_path, exist_ok=True)

    # Генерируем имя файла
    csv_filename = os.path.join(folder_path, f"{table_name}.csv")
    data.to_csv(csv_filename, index=False)  # Сохраняем данные в CSV
    conn.close()


def get_max_user_id(database, table_name):
    """
    Функция для получения максимального user_id

    На входе:
    - database: Имя базы данных
    - table_name: Имя таблицы базы данных

    На выходе:
    - max_id: целое число, максимальное значение user_id. Если таблица пустая или отсутствуют значения user_id, возвращается None
    - 0: если таблица не пуста, но в ней нет user_id
    """
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute(f"SELECT user_id FROM {table_name};")    # Получаем все user_id из таблицы
    user_ids = cursor.fetchall()
    conn.close()

    # Если нет пользователей, возвращаем None
    if not user_ids:
        return None, None
    
    # Определяем max_id
    max_id = 0
    for user_id in user_ids:
        if int(user_id[0]) > max_id:
            max_id = int(user_id[0])

    return max_id if max_id is not None else 0 


def balance_data(table_name, database):
    """
    Балансировка данных в таблице до равного количества записей фейковых и настоящих аккаунтов
    
    На входе:
    - table_name: имя таблицы, в которой происходит аугментация
    - database: имя базы данных

    На выходе:
    - fake_count_before: количество фейков до аугментации
    - real_count_before: количество настоящих аккаунтов до аугментации
    - fake_count_after: количество фейков после аугментации
    - real_count_after: количество настоящих аккаунтов после аугментации
    - augmentation_needed: переменная, показывающая необходимость в аугментации
    - augmented_table_name: имя аугментированной таблицы
    """
    augmentation_needed = False  # Инициализация по умолчанию, если балансировка не требуется (необходима ли аугментация)

    # Подсчет количества записей фейковых и настоящих аккаунтов
    fake_count_before = count_records(database, table_name, "is_fake = 1")
    real_count_before = count_records(database, table_name, "is_fake = 0")
    
    # Если фейков больше настоящих аккаунтов, то увеличиваем количество настоящих
    if fake_count_before > real_count_before:
        table_to_augment = f"{table_name} WHERE is_fake = 0"
        num_rows_to_create = fake_count_before - real_count_before  # Определяем сколько новых настоящих записей нужно создать
        augmentation_needed = True
    # Если настоящих аккаунтов больше фейков, то увеличиваем количество фейков
    elif real_count_before > fake_count_before:
        table_to_augment = f"{table_name} WHERE is_fake = 1"
        num_rows_to_create = real_count_before - fake_count_before  # Определяем сколько новых фейковых записей нужно создать
        augmentation_needed = True
    # Иначе аугментация не требуется
    else:
        fake_count_after = fake_count_before
        real_count_after = real_count_before
        return fake_count_before, real_count_before, fake_count_after, real_count_after, augmentation_needed
    
    # Загрузка данных для аугментации
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_to_augment}")
    data_to_augment = cursor.fetchall()
    
    # Создание списков для значений из каждой строки
    columns = [description[0] for description in cursor.description]  # Получаем имена столбцов
    values_lists = [[] for _ in range(len(columns))]
    for row in data_to_augment:
        for i, value in enumerate(row):
            values_lists[i].append(value)
    
    # Получение максимального значение user_id, чтоб вставлять записи после него
    max_user_id = get_max_user_id(database, table_name)
    
    # Создание новых записей на основе выбора случайных значений из списков
    augmented_data = []
    for _ in range(num_rows_to_create):
        new_user_id = int(max_user_id) + 1
        new_row_values = [new_user_id] + [np.random.choice(values) for values in values_lists[1:]]
        augmented_data.append(new_row_values)
        max_user_id = int(max_user_id) + 1  # Обновление максимального значения user_id с каждой записью
    
    # Сохранение аугментированных данных в новую таблицу базы данных
    save_augmented_data_to_database(table_name, augmented_data, database)

    # Сохранение новых данных в CSV-файл
    augmented_table_name = f"{table_name}_augment"
    save_augmented_data_to_csv(database, augmented_table_name, app_root)

    conn.close()

    # Определение по индексу is_fake, какие данные были аугментированы (фейковые или настоящие)
    is_fake_in_augmented = augmented_data[0][-1]
    
    # Определяем количество аккаунтов после аугментации
    if is_fake_in_augmented == "1":
        fake_count_after = fake_count_before + num_rows_to_create
        real_count_after = real_count_before
    else:
        real_count_after = real_count_before + num_rows_to_create
        fake_count_after = fake_count_before

    return fake_count_before, real_count_before, fake_count_after, real_count_after, augmentation_needed, augmented_table_name
