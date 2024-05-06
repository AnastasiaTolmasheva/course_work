import sqlite3
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import MinMaxScaler
from sklearn.cluster import DBSCAN
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import matplotlib.pyplot as plt
import seaborn as sns
import os


def run_dbscan_algorithm(table_name, eps, min_samples, visualization, folder):
    """
    Алгоритм для нахождения аномалий DBSCAN. Объединяет точки в кластеры, те значения, которые не относятся ни к какому
    кластеру считаются аномалией и фиктивным аккаунтом. Производит рассчет метрик на основе заранее размеченных данных,
    а также выводит найденные аккаунты в CSV файл, по желанию добавляет визуализацию.

    На входе:
    - table_name: название выбранной пользователем таблицы (датасета)
    - eps: параметр алгоритма DBSCAN (определяет окрестности вокруг точек данных)
    - min_samples: параметр алгоритма DBSCAN (минимальное количество соседей в радиусе)
    - visualization: строковое значение с необходимостью визуализации
    - folder: папка, в которую сохраняются результаты работы алгоритма
    """

    connection = sqlite3.connect("app_database_features.db")

    # Чтение данных для DBSCAN из таблицы с характеристиками
    query = f"""
    SELECT user_id,
        username_length,
        numbers_in_name,
        email_length,
        matching_names,
        pattern_email,
        country,
        date_last_email,
        date_registered,
        date_last_login,
        matching_dates,
        username_neighbour_above,
        username_neighbour_below,
        email_neighbour_above,
        email_neighbour_below
    FROM {table_name};
    """
    data = pd.read_sql_query(query, connection)
    data.set_index("user_id", inplace=True)

    # Заполняем нулями пропущенные значения
    imputer = SimpleImputer(strategy="constant", fill_value=0)
    data_imputed = imputer.fit_transform(data)

    # Нормализация признаков: приводим все значения к диапазону от 0 до 1
    # Для каждого столбца определяется минимальное и максимальное значения, 
    # затем каждое значение в этом столбце масштабируется в диапазон 0 - 1
    scaler = MinMaxScaler()
    data_normalized = scaler.fit_transform(data_imputed)

    # Применение DBSCAN
    dbscan = DBSCAN(eps=eps, min_samples=min_samples)
    data["cluster"] = dbscan.fit_predict(data_normalized)

    data["new_cluster"] = 0  # ПРисваиваем индекс 0 для нормальных кластеров (нормальных аккаунтов)
    data.loc[data["cluster"] == -1, "new_cluster"] = 1  # Присваиваем индекс 1 аномалиям

    # Чтение меток is_fake из базы данных
    labels_query = f"SELECT is_fake FROM {table_name};"
    true_labels = pd.read_sql_query(labels_query, connection)['is_fake']

    # Вычисление метрик
    accuracy = accuracy_score(true_labels, data['new_cluster'])
    precision = precision_score(true_labels, data['new_cluster'], average='weighted')
    recall = recall_score(true_labels, data['new_cluster'], average='weighted')
    f1 = f1_score(true_labels, data['new_cluster'], average='weighted')

    # Получение данных из таблицы о найденных фейках
    fake_user_ids = data[data["new_cluster"] == 1].index.tolist()    
    if fake_user_ids:
        query = f"""
        SELECT user_id, is_fake
        FROM {table_name}
        WHERE user_id IN ({','.join(map(str, fake_user_ids))});
        """
        fake_accounts = pd.read_sql_query(query, connection)

        # Сохранение фейковых аккаунтов в CSV-файл
        fake_csv_path = get_unique_filename(f'dbscan_{table_name}_eps_{eps}_min_samples_{min_samples}', '.csv', folder)
        fake_accounts.to_csv(fake_csv_path, index=False)

    # Если требуется визуализация, создаем изображение
    if visualization == "Да":
        plt.figure(figsize=(12, 8))
        sns.scatterplot(x=data.index, y='username_length', hue='cluster', data=data, palette='viridis', legend='full')
        plt.title('Нахождение фейков с помощью метода DBSCAN')
        plt.xlabel('User_id')
        plt.ylabel('Username length')
        plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
        metrics_text = f'Accuracy: {accuracy:.2f}\nPrecision: {precision:.2f}\nRecall: {recall:.2f}\nF1-score: {f1:.2f}'
        plt.text(0.5, 0.8, metrics_text, horizontalalignment='center', verticalalignment='center', 
                 transform=plt.gca().transAxes, fontsize=12, 
                 bbox=dict(facecolor='white', alpha=0.5))
        image_file_path = get_unique_filename(f'dbscan_{table_name}_eps_{eps}_min_samples_{min_samples}', '.png', folder)
        plt.savefig(image_file_path)
        plt.show()

    connection.close()


def get_unique_filename(name, extension, folder):
    """
    Создание уникального имени файла (добавление индекса в конец названия, если файл существует)

    На входе:
    - name: имя файла
    - extension: расширение файла
    - folder: папка, в которую сохраняется результат

    На выходе:
    - full_path: полный путь файла с его названием
    """
    index = 1
    filename = f"{name}{extension}"
    full_path = os.path.join(folder, filename)
    while os.path.exists(full_path):
        filename = f"{name}_{index}{extension}"
        full_path = os.path.join(folder, filename)
        index += 1
    return full_path
