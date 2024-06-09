import sqlite3
import pandas as pd
from sklearn.cluster import DBSCAN
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE
import seaborn as sns
import os


def run_dbscan_algorithm(table_name, eps, min_samples, visualization, folder):
    """
    Алгоритм для нахождения аномалий DBSCAN. Объединяет точки в кластеры, те значения, которые не относятся ни к какому
    кластеру считаются аномалией и фиктивным аккаунтом. Производит рассчет метрик на основе заранее размеченных данных,
    а также выводит найденные аномалии в CSV файл, по желанию добавляет визуализацию.

    На входе:
    - table_name: название выбранной пользователем таблицы (датасета)
    - eps: параметр алгоритма DBSCAN (определяет окрестности вокруг точек данных)
    - min_samples: параметр алгоритма DBSCAN (минимальное количество соседей в радиусе)
    - visualization: строковое значение с необходимостью визуализации
    - folder: папка, в которую сохраняются результаты работы алгоритма
    """
    # Чтение данных для DBSCAN из таблицы с характеристиками
    connection = sqlite3.connect("app_database_features.db")
    query = f"SELECT * FROM {table_name};"
    data = pd.read_sql_query(query, connection, index_col="user_id")
    data_copy = data.copy()
    data = data.drop(columns="is_fake")

    # Применение DBSCAN
    dbscan = DBSCAN(eps=eps, min_samples=min_samples)
    data["cluster"] = dbscan.fit_predict(data)

    data["new_cluster"] = 0  # Присваиваем индекс 0 для нормальных кластеров (нормальных аккаунтов)
    data.loc[data["cluster"] == -1, "new_cluster"] = 1  # Присваиваем индекс 1 аномалиям

    # Получение данных из таблицы о найденных фейках
    data.reset_index(inplace=True)
    fake_user_ids = data[data["new_cluster"] == 1]["user_id"].tolist()
    connection_full = sqlite3.connect("app_database.db") 
    fake_csv_path = get_unique_filename(f"dbscan_{table_name}_eps_{eps}_min_samples_{min_samples}", ".csv", folder)

    # Открываем файл для записи
    with open(fake_csv_path, "w", encoding="utf-8") as fake_csv_file:
        fake_csv_file.write("user_id,username,password,email,url,phone,mailing_address,billing_address,country,locales,date_last_email,date_registered,date_validated,date_last_login,must_change_password,auth_id,auth_str,disabled,disabled_reason,inline_help,gossip,is_fake\n")
        for user_id in fake_user_ids:
            query_single_user = f"SELECT * FROM {table_name} WHERE user_id = {user_id}"
            fake_account_info = pd.read_sql_query(query_single_user, connection_full)
            if not fake_account_info.empty:
                fake_csv_file.write(f"{','.join(map(str, fake_account_info.values.tolist()[0]))}\n")

    connection_full.close()
    connection.close() 

    # Вычисление метрик
    accuracy = accuracy_score(data_copy["is_fake"], data["new_cluster"])
    precision = precision_score(data_copy["is_fake"], data["new_cluster"], pos_label=1)
    recall = recall_score(data_copy["is_fake"], data["new_cluster"], pos_label=1)
    f1 = f1_score(data_copy["is_fake"], data["new_cluster"], pos_label=1)
    metrics_df = pd.DataFrame({"Метрики": ["Accuracy", "Precision", "Recall", "F1-score"],
                            "Значения": [accuracy, precision, recall, f1]})

    # Сохранение метрик в CSV файл
    metrics_csv_path = get_unique_filename(f"dbscan_metrics_{table_name}_eps_{eps}_min_samples_{min_samples}", ".csv", folder)
    metrics_df.to_csv(metrics_csv_path, index=False)

    # Если требуется визуализация, создаем изображение
    if visualization == "Да":
        tsne = TSNE(n_components=2)
        X_tsne = tsne.fit_transform(data)   # Снижение размерности данных
        data["tsne1"] = X_tsne[:, 0]
        data["tsne2"] = X_tsne[:, 1]

        plt.figure(figsize=(12, 8))
        sns.scatterplot(x='tsne1', y='tsne2', hue='new_cluster', data=data, palette={0: 'green', 1: 'red'})
        plt.title("Нахождение фейков с помощью DBSCAN")
        plt.xlabel("")
        plt.ylabel("")
        legend_labels = {'0': 'Норма', '1': 'Фейк'}
        handles, labels = plt.gca().get_legend_handles_labels()
        new_labels = [legend_labels[label] for label in labels]
        plt.legend(handles, new_labels, loc='upper left', bbox_to_anchor=(1, 1), fontsize=12)

        metrics_text = f'Accuracy: {accuracy:.2f}\nPrecision: {precision:.2f}\nRecall: {recall:.2f}\nF1-score: {f1:.2f}'
        plt.text(0.5, 0.5, metrics_text, horizontalalignment='center', fontsize=12, transform=plt.gca().transAxes, bbox=dict(facecolor='white', alpha=0.5))

        image_file_path = get_unique_filename(f"dbscan_{table_name}_eps_{eps}_min_samples_{min_samples}", ".png", folder)
        plt.savefig(image_file_path, bbox_inches="tight")
        plt.show()

        """
        Второй вариант визуализации
        plt.figure(figsize=(12, 8))
        sns.scatterplot(x=data["username_neighbour_above"], y=data["email_neighbour_above"], c=data["new_cluster"], data=data, palette='viridis', legend='full')
        plt.title("Нахождение фейков с помощью DBSCAN")
        plt.xlabel("Соседи по username")
        plt.ylabel("Соседи по email")
        plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
        metrics_text = f'Accuracy: {accuracy:.2f}\nPrecision: {precision:.2f}\nRecall: {recall:.2f}\nF1-score: {f1:.2f}'
        plt.text(0.5, 0.8, metrics_text, horizontalalignment='center', verticalalignment='center', 
                 transform=plt.gca().transAxes, fontsize=12, 
                 bbox=dict(facecolor='white', alpha=0.5))
        image_file_path = get_unique_filename(f'dbscan_{table_name}_eps_{eps}_min_samples_{min_samples}', '.png', folder)
        plt.savefig(image_file_path)
        plt.show()
        """


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
