import sqlite3
import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE
import seaborn as sns
import joblib
import os


def run_isolation_forest_algorithm(table_name, model_if, visualization, folder):
    """
    Алгоритм изоляционного леса для нахождения аномалий. Выбранная модель загружается для предсказаний,
    производится рассчет метрик на основе заранее размеченных данных, 
    найденные аккаунты выводятся в CSV файл, по желанию добавляется визуализация.

    На входе:
    - table_name: название выбранной пользователем таблицы (датасета)
    - model_if: имя модели изоляционного леса
    - visualization: строковое значение с необходимостью визуализации
    - folder: папка, в которую сохраняются результаты работы алгоритма
    """

    # Загрузка модели
    model_path = os.path.join("models", model_if)
    model = joblib.load(model_path)

    # Чтение данных для изоляционного леса из таблицы с признаками
    connection = sqlite3.connect("app_database_features.db")
    query = f"SELECT * FROM {table_name};"
    data = pd.read_sql_query(query, connection, index_col="user_id")
    data_copy = data.copy()
    data = data.drop(columns="is_fake")

    predictions = model.predict(data)

    # Преобразование предсказаний к меткам is_fake (-1 = 1, 1 = 0)
    pred_binary = (predictions == -1).astype(int)
    data_copy["predictions"] = pred_binary

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
    accuracy = accuracy_score(data_copy["is_fake"], data_copy["predictions"])
    precision = precision_score(data_copy["is_fake"], data_copy["predictions"], pos_label=1)
    recall = recall_score(data_copy["is_fake"], data_copy["predictions"], pos_label=1)
    f1 = f1_score(data_copy["is_fake"], data_copy["predictions"], pos_label=1)
    metrics_df = pd.DataFrame({"Метрики": ["Accuracy", "Precision", "Recall", "F1-score"],
                            "Значения": [accuracy, precision, recall, f1]})

    # Сохранение метрик в CSV файл
    metrics_csv_path = get_unique_filename(f"{model}_metrics_{table_name}", ".csv", folder)
    metrics_df.to_csv(metrics_csv_path, index=False)

    # Если требуется визуализация, создается изображение
    if visualization == "Да":
        tsne = TSNE(n_components=2)
        X_tsne = tsne.fit_transform(data_copy) # Снижение размерности данных

        # Добавление сниженных данных в исходные
        data_copy["tsne1"] = X_tsne[:, 0]
        data_copy["tsne2"] = X_tsne[:, 1]

        plt.figure(figsize=(10, 8))
        sns.scatterplot(x='tsne1', y='tsne2', hue=pred_binary, data=data_copy, palette={0: 'green', 1: 'red'})
        plt.title("Нахождение фейков с помощью изоляционного леса")
        plt.xlabel("")
        plt.ylabel("")
        legend_labels = {'0': 'Норма', '1': 'Фейк'}
        handles, labels = plt.gca().get_legend_handles_labels()
        new_labels = [legend_labels[label] for label in labels]
        plt.legend(handles, new_labels, loc='upper left', bbox_to_anchor=(1, 1), fontsize=12)

        metrics_text = f'Accuracy: {accuracy:.2f}\nPrecision: {precision:.2f}\nRecall: {recall:.2f}\nF1-score: {f1:.2f}'
        plt.text(0.5, 0.5, metrics_text, horizontalalignment='center', fontsize=12, transform=plt.gca().transAxes, bbox=dict(facecolor='white', alpha=0.5))

        image_file_path = get_unique_filename(f"{model}_{table_name}", ".png", folder)
        plt.savefig(image_file_path, bbox_inches="tight")
        plt.show()


        """
        Второй вариант визуализации
        plt.figure(figsize=(12, 8))
        plt.scatter(X_test["time_difference"], X_test["numbers_in_name"], c=pred_binary, cmap="viridis")
        plt.xlabel("Разница во времени регистрации и последнего входа")
        plt.ylabel("Доля чисел в имени")
        plt.title("Нахождение фейков с помощью изоляционного леса")
        plt.colorbar()
        metrics_text = f'Accuracy: {accuracy:.2f}\nPrecision: {precision:.2f}\nRecall: {recall:.2f}\nF1-score: {f1:.2f}'
        plt.text(0.5, 0.8, metrics_text, horizontalalignment='center', verticalalignment='center', 
                transform=plt.gca().transAxes, fontsize=12, 
                bbox=dict(facecolor='white', alpha=0.5))
        image_file_path = get_unique_filename(f'isolation_forest_{table_name}_test_{test_dataset_fraction}', '.png', folder)
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
