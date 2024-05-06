import sqlite3
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
import joblib
import os


def run_isolation_forest_algorithm(table_name, test_dataset_fraction, visualization, folder):
    """
    Алгоритм леса изоляции для нахождения аномалий. Создается и обучается модель, 
    далее предсказывает метки на тестовых данных. Производит рассчет метрик на основе 
    заранее размеченных данных, а также выводит найденные аккаунты в CSV файл, 
    по желанию добавляет визуализацию.

    На входе:
    - table_name: название выбранной пользователем таблицы (датасета)
    - test_dataset_fraction: объем тестовой выборки
    - visualization: строковое значение с необходимостью визуализации
    - folder: папка, в которую сохраняются результаты работы алгоритма
    """
    connection = sqlite3.connect("app_database_features.db")

    # Чтение данных для леса изоляции из таблицы с признаками
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
        email_neighbour_below,
        is_fake
    FROM {table_name};
    """
    data = pd.read_sql_query(query, connection)

    # Разделение на X (признаки) и y (целевую переменную)
    X = data.drop(columns=["is_fake"])  # Признаки
    y = data["is_fake"]  # Размеченные данные

    # Разделение на обучающие и тестовые данные
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_dataset_fraction, random_state=42, stratify=y)

    # Заполнение пропущенных значений нулями
    imputer = SimpleImputer(strategy='constant', fill_value=0)
    X_train_imputed = imputer.fit_transform(X_train)
    X_test_imputed = imputer.transform(X_test)

    # Стандартизация данных: преобразуем данные таким образом, чтобы их среднее значение стало равно 0, 
    # а стандартное отклонение - 1 для каждого столбца. 
    scaler = StandardScaler()
    X_train_normalized = scaler.fit_transform(X_train_imputed)
    X_test_normalized = scaler.transform(X_test_imputed)

    # Обучение модели Isolation Forest
    model = IsolationForest(contamination="auto")
    model.fit(X_train_normalized)

    # Проверяем, существует ли папка "models"
    if not os.path.exists("models"):
        os.makedirs("models")

    # Сохранение обученной модели в папку "models"
    model_filename = f"models/model_{table_name}_test_{test_dataset_fraction}.pkl"
    joblib.dump(model, model_filename)

    # Предсказания на тестовых данных
    predictions = model.predict(X_test_normalized)

    # Преобразование предсказаний к меткам is_fake (-1 = 1, 1 = 0)
    pred_binary = (predictions == -1).astype(int)

    # Вычисление метрик
    accuracy = accuracy_score(y_test, pred_binary)
    precision = precision_score(y_test, pred_binary, average="weighted")
    recall = recall_score(y_test, pred_binary, average="weighted")
    f1 = f1_score(y_test, pred_binary, average="weighted")

    # Определение фейков (аномалий)
    fake_user_ids = X_test[predictions == -1]["user_id"].tolist()

    # Сохранение информации о фейках в CSV файл
    if fake_user_ids:
        fake_query = f"""
        SELECT user_id, is_fake
        FROM {table_name}
        WHERE user_id IN ({','.join(map(str, fake_user_ids))});
        """
        fake_accounts = pd.read_sql_query(fake_query, connection)

        # Сохранение фейковых аккаунтов в CSV
        fake_csv_path = os.path.join(folder, f"isolation_forest_{table_name}_test_{test_dataset_fraction}.csv")
        fake_accounts.to_csv(fake_csv_path, index=False)

    # Если требуется визуализация, создаем изображение
    if visualization == "Да":
        plt.figure(figsize=(10, 6))
        plt.scatter(X_test["user_id"], X_test["username_length"], c=pred_binary, cmap="viridis")
        plt.xlabel("User ID")
        plt.ylabel("Username length")
        plt.title("Нахождение фейков с помощью леса изоляции")
        plt.colorbar()
        metrics_text = f'Accuracy: {accuracy:.2f}\nPrecision: {precision:.2f}\nRecall: {recall:.2f}\nF1-score: {f1:.2f}'
        plt.text(0.5, 0.8, metrics_text, horizontalalignment='center', verticalalignment='center', 
                 transform=plt.gca().transAxes, fontsize=12, 
                 bbox=dict(facecolor='white', alpha=0.5))
        image_file_path = get_unique_filename(f'isolation_forest_{table_name}_test_{test_dataset_fraction}', '.png', folder)
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
