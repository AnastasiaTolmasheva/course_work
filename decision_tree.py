
import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn import tree
import matplotlib.pyplot as plt
import sqlite3
import os
import joblib


def run_decision_tree_algorithm(table_name, model_dt, visualization, folder):
    """
    Алгоритм дерева решений для классификации. Принимается обученная модель, которая 
    предсказывает метки на тестовых данных. Производится рассчет метрик на основе 
    заранее размеченных данных, найденные аномалии выводятся в CSV файл, 
    по желанию добавляется визуализация.

    На входе:
    - table_name: название выбранной пользователем таблицы (датасета)
    - model_dt: имя модели дерева решений
    - visualization: строковое значение с необходимостью визуализации
    - folder: папка, в которую сохраняются результаты работы алгоритма
    """
    # Загрузка модели
    model_path = os.path.join("models", model_dt)
    model = joblib.load(model_path)

    # Чтение данных для дерева решений из таблицы с признаками
    connection = sqlite3.connect("app_database_features.db")
    query = f"SELECT * FROM {table_name};"
    data = pd.read_sql_query(query, connection, index_col="user_id")
    data_copy = data.copy()
    X = data.drop(columns="is_fake")
    y = data["is_fake"]

    # Создание предсказаний
    predictions = model.predict(X)
    data_copy["predictions"] = predictions

    # Получение данных из таблицы о найденных фейках
    data_copy.reset_index(inplace=True)
    fake_user_ids = data_copy[data_copy["predictions"] == 1]["user_id"].tolist()
    connection_full = sqlite3.connect("app_database.db")
    fake_csv_path = get_unique_filename(f"{model}_{table_name}", ".csv", folder) 

    # Открываем файл для записи
    with open(fake_csv_path, "w", encoding="utf-8") as fake_csv_file:
        fake_csv_file.write("user_id,username,password,email,url,phone,mailing_address,billing_address,country,locales,date_last_email,date_registered,date_validated,date_last_login,must_change_password,auth_id,auth_str,disabled,disabled_reason,inline_help,gossip,is_fake\n")
        for user_id in fake_user_ids:
            query_single_user = f"SELECT * FROM {table_name} WHERE user_id = {user_id}"
            fake_account_info = pd.read_sql_query(query_single_user, connection_full)
            fake_csv_file.write(f"{','.join(map(str, fake_account_info.values.tolist()[0]))}\n")

    connection_full.close()
    connection.close() 

    # Вычисление метрик
    accuracy = accuracy_score(y, predictions)
    precision = precision_score(y, predictions, pos_label=1)
    recall = recall_score(y, predictions, pos_label=1)
    f1 = f1_score(y, predictions, pos_label=1)
    metrics_df = pd.DataFrame({"Метрики": ["Accuracy", "Precision", "Recall", "F1-score"],
                            "Значения": [accuracy, precision, recall, f1]})

    # Сохранение метрик в CSV файл
    metrics_csv_path = get_unique_filename(f"{model}_metrics_{table_name}", ".csv", folder)
    metrics_df.to_csv(metrics_csv_path, index=False)

    if visualization == "Да":  # Визуализация дерева решений
        plt.figure(figsize=(20, 10))
        tree.plot_tree(model, feature_names=X.columns, class_names=["Not Fake", "Fake"], filled=True)
        metrics_text = f'Accuracy: {accuracy:.2f}\nPrecision: {precision:.2f}\nRecall: {recall:.2f}\nF1-score: {f1:.2f}'
        plt.text(1, 0.5, metrics_text, horizontalalignment='center', fontsize=12, transform=plt.gca().transAxes, bbox=dict(facecolor='white', alpha=0.5))
        image_file_path = get_unique_filename(f"{model}_{table_name}", ".png", folder)
        plt.savefig(image_file_path, bbox_inches="tight")
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
