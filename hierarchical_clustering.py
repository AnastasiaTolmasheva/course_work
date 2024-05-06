import sqlite3
import pandas as pd
import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from scipy.cluster.hierarchy import linkage, dendrogram
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.cluster import AgglomerativeClustering
import matplotlib.pyplot as plt
import os


def find_optimal_clusters(data_normalized, true_labels, linkage_method):
    """
    Поиск оптимального количества кластеров

    На входе:
    - data_normalized: нормализованные данные
    - true_labels: метки is_fake
    - linkage_method: метод соединения (способ, которым алгоритм кластеризации объединяет
    отдельные объекты или кластеры в более крупные кластеры)

    На выходе:
    - optimal_clusters: оптимальное число кластеров
    """
    k_values = range(2, 10)
    metrics_scores = {
        'accuracy': [],
        'precision': [],
        'recall': [],
        'f1': []
    }

    for k in k_values:
        model = AgglomerativeClustering(n_clusters=k, linkage=linkage_method)
        labels = model.fit_predict(data_normalized)

        # Преобразуем метки в бинарные
        unique_clusters, cluster_counts = np.unique(labels, return_counts=True)
        min_cluster_size = min(cluster_counts)
        outlier_clusters = unique_clusters[cluster_counts == min_cluster_size]
        binary_labels = np.zeros_like(labels)
        binary_labels[np.isin(labels, outlier_clusters)] = 1

        # Вычисляем метрики
        metrics_scores['accuracy'].append(accuracy_score(true_labels['is_fake'], binary_labels))
        metrics_scores['precision'].append(precision_score(true_labels['is_fake'], binary_labels, average='weighted'))
        metrics_scores['recall'].append(recall_score(true_labels['is_fake'], binary_labels, average='weighted'))
        metrics_scores['f1'].append(f1_score(true_labels['is_fake'], binary_labels, average='weighted'))

    # Выбор оптимального числа кластеров на основе максимальной accuracy
    optimal_clusters = k_values[np.argmax(metrics_scores['accuracy'])]

    return optimal_clusters


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
    connection = sqlite3.connect('app_database_features.db')

    # Чтение данных для агломеративной кластеризации из таблицы с признаками
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
    data.set_index('user_id', inplace=True)

    # Заполнение пропущенных значений нулями
    imputer = SimpleImputer(strategy='constant', fill_value=0)
    data_imputed = imputer.fit_transform(data)

    # Стандартизация данных: преобразуем данные таким образом, чтобы их среднее значение стало равно 0, 
    # а стандартное отклонение - 1 для каждого столбца. 
    scaler = StandardScaler()
    data_normalized = scaler.fit_transform(data_imputed)

    # Получение меток is_fake
    true_labels = pd.read_sql_query(f"SELECT user_id, is_fake FROM {table_name}", connection)

    # Нахождение оптимального числа кластеров
    optimal_clusters = find_optimal_clusters(data_normalized, true_labels, linkage_method)

    # Применение агломеративной кластеризации
    final_model = AgglomerativeClustering(n_clusters=optimal_clusters, linkage=linkage_method)
    data['cluster'] = final_model.fit_predict(data_normalized)

    # Определение аномальных кластеров: определяем размер кластера, если он меньше 1/5 максимального размера кластеров, то считаем его аномальным
    unique_clusters, cluster_counts = np.unique(data['cluster'], return_counts=True)
    max_cluster_size = max(cluster_counts)
    outlier_clusters = unique_clusters[cluster_counts < max_cluster_size / 5]
    data['is_anomaly'] = 0
    data.loc[data['cluster'].isin(outlier_clusters), 'is_anomaly'] = 1


    # Объединение данных с метками is_fake
    merged_data = data.merge(true_labels, left_index=True, right_on='user_id')

    # Вычисление метрик
    accuracy = accuracy_score(merged_data['is_fake'], merged_data['is_anomaly'])
    precision = precision_score(merged_data['is_fake'], merged_data['is_anomaly'], average='weighted')
    recall = recall_score(merged_data['is_fake'], merged_data['is_anomaly'], average='weighted')
    f1 = f1_score(merged_data['is_fake'], merged_data['is_anomaly'], average='weighted')

    # Сохранение информации о фейках в CSV файл
    fake_user_ids = data[data['cluster'].isin(outlier_clusters)].index.tolist()
    if fake_user_ids:
        fake_query = f"""
        SELECT user_id, is_fake 
        FROM {table_name} 
        WHERE user_id IN ({','.join(map(str, fake_user_ids))})
        """
        fake_accounts = pd.read_sql_query(fake_query, connection)
        fake_csv_path = get_unique_filename(f'hierarchical_{table_name}_{linkage_method}', '.csv', folder)
        fake_accounts.to_csv(fake_csv_path, index=False)

    # Визуализация дендрограммы, если требуется визуализация
    if visualization == 'Да':
        Z = linkage(data_normalized, method=linkage_method)
        plt.figure(figsize=(12, 8))
        plt.title(f"Дендрограмма агломеративной кластеризации ({linkage_method} linkage)")
        dendrogram(
            Z,
            orientation='top',
            labels=data.index.tolist(),
            color_threshold=0.7 * max(Z[:, 2]),
            show_leaf_counts=True,
        )
        metrics_text = f'Accuracy: {accuracy:.2f}\nPrecision: {precision:.2f}\nRecall: {recall:.2f}\nF1-score: {f1:.2f}'
        plt.text(0.5, 0.8, metrics_text, horizontalalignment='center', verticalalignment='center', 
                 transform=plt.gca().transAxes, fontsize=12, 
                 bbox=dict(facecolor='white', alpha=0.5))
        dendrogram_path = get_unique_filename(f'dendrogram_{table_name}_{linkage_method}', '.png', folder)
        plt.savefig(dendrogram_path)
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
    while os.path.exists(os.path.join(folder, filename)):
        filename = f"{name}_{index}{extension}"
        index += 1
    return os.path.join(folder, filename)
