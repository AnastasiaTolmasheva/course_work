import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
import joblib
import os
from augmentation import balance_data
from augmentation import making_features


app_root = os.getcwd()
teaching_dir = os.path.join(app_root, "teaching")


def teaching_models(file_name, algorithm, param_grid):
    """
    Функция для обучения и сохранения моделей алгоритмов изоляционного леса,
    дерева решений и случайного леса. Сохраняет модели в папку models.

    На вход:
    - file_name: имя файла, на основе которого модель обучается
    - algorithm: название алгоритма
    - param_grid: список словарей с параметрами модели
    """
    file_path = os.path.join(app_root, "datasets", file_name)
    data = pd.read_csv(file_path)

    y = data["is_fake"]  # Размеченные данные
    X = data.drop(columns=["is_fake", "user_id"])  # Признаки

    if algorithm == "isol_for":
        model_class = IsolationForest
    elif algorithm == "rand_for":
        model_class = RandomForestClassifier
    elif algorithm == "dec_tree":
        model_class = DecisionTreeClassifier
    else:
        raise ValueError("Неверное название алгоритма")

    table_name = file_name[:-4]
    for params in param_grid:
        model = model_class(**params)
        if algorithm == "isol_for":
            model.fit(X)
        else:
            model.fit(X, y)
        models_dir = os.path.join(app_root, "models")
        if not os.path.exists(models_dir):
            os.makedirs(models_dir)
        model_filename = os.path.join(models_dir, f"{algorithm}_{table_name}")
        for key, value in params.items():
            model_filename += f"{key}_{value}_"
        model_filename += ".pkl"
        joblib.dump(model, model_filename)


# Параметры для моделей
param_grid_if = [
    {'n_estimators': 50, 'contamination': 'auto', 'random_state': 42},
    {'n_estimators': 100, 'contamination': 'auto', 'random_state': 42},
    {'n_estimators': 150, 'contamination': 'auto', 'random_state': 42},
    {'n_estimators': 200, 'contamination': 'auto', 'random_state': 42},
    {'n_estimators': 100, 'contamination': 0.1, 'random_state': 42},
    {'n_estimators': 100, 'contamination': 0.2, 'random_state': 42},
    {'n_estimators': 100, 'contamination': 0.3, 'random_state': 42}, 
    {'n_estimators': 100, 'contamination': 0.4, 'random_state': 42},
    {'n_estimators': 100, 'contamination': 0.5, 'random_state': 42},
]

param_grid_rf = [
    {'n_estimators': 50, 'random_state': 42},
    {'n_estimators': 100, 'random_state': 42},
    {'n_estimators': 150, 'random_state': 42},
    {'n_estimators': 200, 'random_state': 42},
    {'n_estimators': 250, 'random_state': 42},
    {'n_estimators': 300, 'random_state': 42},
    {'n_estimators': 350, 'random_state': 42},
    {'n_estimators': 400, 'random_state': 42},
]

param_grid_dt = [
    {'criterion': 'gini', 'splitter': 'best', 'random_state': 42},
    {'criterion': 'entropy', 'splitter': 'best', 'random_state': 42},
]


os.chdir(teaching_dir)
balance_data("dataset.csv")
making_features("dataset.csv")
making_features("dataset_augment.csv")

teaching_models("dataset_features.csv", "dec_tree", param_grid_dt)
teaching_models("dataset_features.csv", "rand_for", param_grid_rf)
teaching_models("dataset_features.csv", "isol_for", param_grid_if)
teaching_models("dataset_augment_features.csv", "dec_tree", param_grid_dt)
teaching_models("dataset_augment_features.csv", "rand_for", param_grid_rf)
teaching_models("dataset_augment_features.csv", "isol_for", param_grid_if)

print("Все модели сохранены.")
