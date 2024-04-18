import numpy as np
import sqlite3


def count_records(database, table_name, condition):
    """
    Подсчет количества записей в таблице базы данных
    
    На входе:
    - database: Путь к файлу базы данных
    - table_name: Название таблицы
    - condition: Условие для фильтрации записей
    
    На выходе:
    - Количество записей в таблице, удовлетворяющих условию
    """
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    query = f"SELECT COUNT(*) FROM {table_name} WHERE {condition};"
    cursor.execute(query)
    count = cursor.fetchone()[0]
    conn.close()
    return count


def save_augmented_data_to_database(original_table_name, augmented_data, database):
    """
    Сохраняет аугментированные данные в новую таблицу в базе данных
    
    На входе:
    - original_table_name: Название оригинальной таблицы в базе данных
    - augmented_data: Аугментированные данные для сохранения
    - database: Имя базы данных
    """
    # Получение информации о столбцах оригинальной таблицы
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    
    # Удаление существующей таблицы, если она существует
    cursor.execute(f"DROP TABLE IF EXISTS {original_table_name}_augment")

    cursor.execute(f"PRAGMA table_info({original_table_name})")
    columns = cursor.fetchall()
    column_names = ', '.join([col[1] for col in columns])
    create_table_query = f"CREATE TABLE IF NOT EXISTS {original_table_name}_augment ({column_names})"
    cursor.execute(create_table_query)
        
    # Копирование данных из оригинальной таблицы
    cursor.execute(f"INSERT INTO {original_table_name}_augment SELECT * FROM {original_table_name}")
    
    # Добавление аугментированных данных в конец таблицы
    for row in augmented_data:
        placeholders = ', '.join(['?' for _ in row])
        cursor.execute(f"INSERT INTO {original_table_name}_augment VALUES ({placeholders})", row)
    
    # Сохранение изменений
    conn.commit()
    
    # Прекращение соединения с базой данных
    conn.close()


def get_max_user_id(database, original_name):
    """
    Функция для получения максимального user_id

    На входе:
    - database: Имя базы данных
    - original_name: Имя таблицы базы данных

    На выходе:
    - max_id: целое число, максимальное значение user_id. Если таблица пустая или отсутствуют значения user_id, возвращается None
    - 0: если таблица не пуста, но в ней нет user_id
    """
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    # Получаем все user_id из таблицы
    cursor.execute(f"SELECT user_id FROM {original_name};")
    user_ids = cursor.fetchall()
    conn.close()

    # Если нет пользователей, возвращаем None
    if not user_ids:
        return None, None
    
    max_id = 0
    for user_id in user_ids:
        if int(user_id[0]) > max_id:
            max_id = int(user_id[0])

    return max_id if max_id is not None else 0 


def balance_data(original_table_name, database):
    """
    Балансирует данные в таблице до равного количества записей фейковых и настоящих аккаунтов
    
    На входе:
    - original_table_name: Имя оригинальной таблицы
    - database: Имя базы данных
    """
    # Подсчет количества записей фейковых и настоящих аккаунтов
    fake_count = count_records(database, original_table_name, "fake = 1")
    real_count = count_records(database, original_table_name, "fake = 0")
    
    # Определение, какую часть данных нужно расширить
    if fake_count > real_count:
        table_to_augment = f"{original_table_name} WHERE fake = 0"
        num_rows_to_create = fake_count - real_count  # Определяем сколько новых настоящих записей нужно создать
    elif real_count > fake_count:
        table_to_augment = f"{original_table_name} WHERE fake = 1"
        num_rows_to_create = real_count - fake_count  # Определяем сколько новых фейковых записей нужно создать
    else:
        print("Количество фейковых аккаунтов и настоящих аккаунтов уже сбалансировано.")
        return
    
    # Загрузка данных для аугментации
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_to_augment}")
    data_to_augment = cursor.fetchall()
    
    # Создаем списки для значений из каждой строки
    columns = [description[0] for description in cursor.description]  # Получаем имена столбцов
    values_lists = [[] for _ in range(len(columns))]
    for row in data_to_augment:
        for i, value in enumerate(row):
            values_lists[i].append(value)
    
    # Получаем максимальное значение user_id
    max_user_id = get_max_user_id(database, original_table_name)
    
    # Создание новых записей на основе выбора случайных значений из списков
    augmented_data = []
    for _ in range(num_rows_to_create):
        new_user_id = int(max_user_id) + 1
        new_row_values = [new_user_id] + [np.random.choice(values) for values in values_lists[1:]]
        augmented_data.append(new_row_values)
        max_user_id = int(max_user_id) + 1  # Обновления максимального значения user_id
    
    # Сохранение аугментированных данных в новую таблицу
    save_augmented_data_to_database(original_table_name, augmented_data, database)
    
    # Вывод результатов после аугментации в консоль
    print("Количество фейковых аккаунтов после аугментации:", fake_count + num_rows_to_create)
    print("Количество настоящих аккаунтов после аугментации:", real_count)
    print("Общее количество данных после аугментации:", fake_count + real_count + num_rows_to_create)

    # Закрытие соединения с базой данных
    conn.close()

