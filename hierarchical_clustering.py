import sqlite3
import pandas as pd
import numpy as np
from scipy.cluster.hierarchy import linkage, dendrogram
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.cluster import AgglomerativeClustering
import matplotlib.pyplot as plt
import os


def find_optimal_clusters(data, linkage_method):
    """
    Поиск оптимального количества кластеров

    На входе:
    - data: данные
    - linkage_method: метод соединения (способ, которым алгоритм кластеризации объединяет
    отдельные объекты или кластеры в более крупные кластеры)

    На выходе:
    - optimal_clusters: оптимальное число кластеров
    - Z: матрица расстояний для построения дендрограммы
    """
    # Используем linkage для создания дендрограммы
    Z = linkage(data, method=linkage_method)

    # Автоматически определяем оптимальное количество кластеров по дендрограмме
    # Выбираем расстояние таким образом, чтобы оно было максимальным, но при этом не превышало порог (0.7 максимального расстояния)
    max_distance = 0.7 * np.max(Z[:, 2])
    optimal_clusters = len(Z[Z[:, 2] > max_distance]) + 1  # Плюс один, так как индексация начинается с 0

    return optimal_clusters, Z


def run_hierarchical_clustering(table_name, linkage_method, visualization, folder):
    """
    Алгоритм для нахождения аномалий агломеративная кластеризация. Находит небольшие кластеры, считает их аномалиями.
    Производит рассчет метрик на основе заранее размеченных данных, а также выводит найденные аккаунты в CSV файл, 
    по желанию добавляет визуализацию.

    На входе:
    - table_name: название выбранной пользователем таблицы (датасета)
    - linkage_method: метод соединения
    - visualization: строковое значение с необходимостью визуализации
    - folder: папка, в которую сохраняются результаты работы алгоритма
    """
    # Чтение данных для агломеративной кластеризации из таблицы с признаками
    connection = sqlite3.connect("app_database_features.db")
    query = f"SELECT * FROM {table_name};"
    data = pd.read_sql_query(query, connection, index_col="user_id")
    data_copy = data.copy()
    data = data.drop(columns="is_fake")

    # Нахождение оптимального числа кластеров
    optimal_clusters, Z = find_optimal_clusters(data, linkage_method)

    # Применение агломеративной кластеризации
    final_model = AgglomerativeClustering(n_clusters=optimal_clusters, linkage=linkage_method)
    data["cluster"] = final_model.fit_predict(data)

    # Определение аномальных кластеров: определяем размер кластера, если он меньше 1/5 размера максимального кластера, то считаем его аномальным
    unique_clusters, cluster_counts = np.unique(data["cluster"], return_counts=True)
    max_cluster_size = max(cluster_counts)
    outlier_clusters = unique_clusters[cluster_counts <= max_cluster_size / 5]
    data["is_anomaly"] = 0
    data.loc[data["cluster"].isin(outlier_clusters), "is_anomaly"] = 1

    # Получение данных из таблицы о найденных фейках
    data.reset_index(inplace=True)
    fake_user_ids = data[data["is_anomaly"] == 1]["user_id"].tolist()
    connection_full = sqlite3.connect("app_database.db") 
    fake_csv_path = get_unique_filename(f"hierarchical_{table_name}_{linkage_method}", ".csv", folder)

    # Открываем файл для записи
    with open(fake_csv_path, "w", encoding="utf-8") as fake_csv_file:
        fake_csv_file.write("user_id,username,password,email,url,phone,mailing_address,billing_address,country,locales,date_last_email,date_registered,date_validated,date_last_login,must_change_password,auth_id,auth_str,disabled,disabled_reason,inline_help,gossip,is_fake\n")
        for user_id in fake_user_ids:
            query_single_user = f"SELECT * FROM {table_name} WHERE user_id = {user_id}"
            fake_account_info = pd.read_sql_query(query_single_user, connection_full)
            if not fake_account_info.empty:
                fake_csv_file.write(f"{','.join(map(str, fake_account_info.values.tolist()[0]))}\n")

    # Вычисление метрик
    accuracy = accuracy_score(data_copy["is_fake"], data["is_anomaly"])
    precision = precision_score(data_copy["is_fake"], data["is_anomaly"], pos_label=1)
    recall = recall_score(data_copy["is_fake"], data["is_anomaly"], pos_label=1)
    f1 = f1_score(data_copy["is_fake"], data["is_anomaly"], pos_label=1)
    metrics_df = pd.DataFrame({"Метрики": ["Accuracy", "Precision", "Recall", "F1-score"],
                            "Значения": [accuracy, precision, recall, f1]})
    
    # Сохранение метрик в CSV файл
    metrics_csv_path = get_unique_filename(f"hierarchical_metrics_{table_name}_{linkage_method}", ".csv", folder)
    metrics_df.to_csv(metrics_csv_path, index=False)
    connection_full.close()
    connection.close()

    # Визуализация дендрограммы
    if visualization == "Да":
        plt.figure(figsize=(12, 8))
        plt.title(f"Дендрограмма агломеративной кластеризации ({linkage_method} linkage)")
        dendrogram(
            Z,
            orientation='top',
            labels=data["user_id"].astype(str).values,
        )
        metrics_text = f'Accuracy: {accuracy:.2f}\nPrecision: {precision:.2f}\nRecall: {recall:.2f}\nF1-score: {f1:.2f}'
        plt.text(0.5, 0.8, metrics_text, horizontalalignment='center', verticalalignment='center', 
                 transform=plt.gca().transAxes, fontsize=12, 
                 bbox=dict(facecolor='white', alpha=0.5))
        dendrogram_path = get_unique_filename(f"dendrogram_{table_name}_{linkage_method}", ".png", folder)
        plt.savefig(dendrogram_path)
        plt.show()


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