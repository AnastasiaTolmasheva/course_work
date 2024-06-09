import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import os
from tkinter.filedialog import askdirectory
import sqlite3
import DBSCAN
import isolation_forest
import hierarchical_clustering
import decision_tree
import random_forest
from features import making_features


class FindFakesScreen(tk.Toplevel):
    def __init__(self, master):
        """
        Инициализация экрана настроек алгоритмов

        На входе:
        - master: главное окно приложения
        """
        super().__init__(master)
        self.title("Настройки")
        self.geometry("900x480")
        self.resizable(False, False)

        # Стиль для кнопок
        style_first = ttk.Style()
        style_first.configure("Second.TButton", font=('Helvetica', 14))

        # Заголовок окна
        title_label = ttk.Label(self, text="Настройки алгоритмов", font=("Helvetica", 18))
        title_label.pack(pady=30)

        # Основной контейнер для фреймов
        main_frame = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_frame.pack(expand=False, fill=tk.X, padx=10, pady=5)

        # Фрейм для размещения полей ввода
        input_frame = ttk.Frame(main_frame)
        main_frame.add(input_frame, weight=1)

        # Фрейм для размещения дополнительных полей
        extra_frame = ttk.Frame(main_frame)
        main_frame.add(extra_frame, weight=15)

        # Фрейм для размещения виджетов выбора папки
        folder_frame = ttk.Frame(self)
        folder_frame.pack(fill="x", padx=10)

        # Фрейм для кнопки Поиска фейков 
        button_frame = ttk.Frame(self)
        button_frame.pack(fill="x", padx=10, pady=50)

        # Комбобокс для выбора алгоримта
        self.algorithm_label = ttk.Label(input_frame, text="Алгоритм:", font=("Helvetica", 14))
        self.algorithm_label.grid(row=0, column=0, padx=30, pady=15, sticky="ew")
        self.algorithm_combobox = ttk.Combobox(input_frame, values=["Изоляционный лес", "DBSCAN", "Иерархическая кластеризация", "Дерево решений", "Случайный лес"], state="readonly", width=25, font=("Helvetica", 14))
        self.algorithm_combobox.grid(row=0, column=1, padx=0, pady=15, sticky="ew")
        self.algorithm_combobox.bind("<<ComboboxSelected>>", self.algorithm_select)
        self.algorithm_combobox.set("Изоляционный лес")  # Выбор алгоритма по умолчанию

        # Комбобокс для выбора датасета
        self.data_label = ttk.Label(input_frame, text="Данные:", font=("Helvetica", 14))
        self.data_label.grid(row=1, column=0, padx=30, pady=15, sticky="ew")
        self.dataset_combobox = ttk.Combobox(input_frame, state="readonly", font=("Helvetica", 14))
        self.dataset_combobox.bind("<<ComboboxSelected>>", self.load_dataset_combobox())
        self.dataset_combobox.grid(row=1, column=1, padx=0, pady=15, sticky="ew")

        # Комбобокс для выбора визуализации
        self.visualization_label = ttk.Label(input_frame, text="Визуализация:", font=("Helvetica", 14))
        self.visualization_label.grid(row=2, column=0, padx=30, pady=15, sticky="ew")
        self.visualization_combobox = ttk.Combobox(input_frame, values=["Да", "Нет"], state="readonly", font=("Helvetica", 14))
        self.visualization_combobox.grid(row=2, column=1, padx=0, pady=15, sticky="ew")
        self.visualization_combobox.set("Да")  # Выбор варианта по умолчанию

        # Выбор папки для вывода результатов
        self.results_label = ttk.Label(folder_frame, text="Вывод результатов:", font=("Helvetica", 14))
        self.results_label.grid(row=0, column=0, padx=30, pady=15, sticky="ew")
        self.selected_folder_entry = ttk.Entry(folder_frame, font=("Helvetica", 14), width=22)
        self.selected_folder_entry.grid(row=0, column=1, padx=0, pady=15, sticky="ew")
        self.select_folder_button = ttk.Button(folder_frame, text="Выбрать", style='Second.TButton', command=self.choose_folder)
        self.select_folder_button.grid(row=0, column=2, padx=21.5, pady=15, sticky="ew")

        # Кнопка для нахождения фейков
        self.find_fakes_button = ttk.Button(button_frame, text="Найти фейки", style='Second.TButton', command=self.find_fakes, width=20)
        self.find_fakes_button.pack()

        # Дополнительные поля для DBSCAN: выбор параметров eps и min_samples
        self.dbscan_eps_label = ttk.Label(extra_frame, text="Eps:", font=("Helvetica", 14))
        self.dbscan_eps_entry = ttk.Entry(extra_frame, font=("Helvetica", 14), width=15)
        self.dbscan_min_samples_label = ttk.Label(extra_frame, text="Min Samples:", font=("Helvetica", 14))
        self.dbscan_min_samples_entry = ttk.Entry(extra_frame, font=("Helvetica", 14), width=15)

        # Дополнительные поля для изоляционного леса: выбор модели 
        self.model_label_if = ttk.Label(extra_frame, text="Модель:", font=("Helvetica", 14))
        self.model_combobox_if = ttk.Combobox(extra_frame, state="readonly", font=("Helvetica", 14), width=15)
        self.model_combobox_if.bind("<<ComboboxSelected>>", self.load_model_combobox())

        # Дополнительные поля для Иерархической кластеризации: выбор метода соединения
        self.hierarchical_linkage_label = ttk.Label(extra_frame, text="Метод соединения:", font=("Helvetica", 14))
        self.hierarchical_linkage_combobox = ttk.Combobox(extra_frame, values=["single", "complete", "average", "ward"], state="readonly", font=("Helvetica", 14), width=10)
        self.hierarchical_linkage_combobox.set("single")

        # Дополнительные поля для Дерева решений: выбор модели 
        self.model_label_dt = ttk.Label(extra_frame, text="Модель:", font=("Helvetica", 14))
        self.model_combobox_dt = ttk.Combobox(extra_frame, state="readonly", font=("Helvetica", 14), width=15)
        self.model_combobox_dt.bind("<<ComboboxSelected>>", self.load_model_combobox())

        # Дополнительные поля для Случайного леса: выбор модели 
        self.model_label_rf = ttk.Label(extra_frame, text="Модель:", font=("Helvetica", 14))
        self.model_combobox_rf = ttk.Combobox(extra_frame, state="readonly", font=("Helvetica", 14), width=15)
        self.model_combobox_rf.bind("<<ComboboxSelected>>", self.load_model_combobox())

        # Вызываем метод, чтобы отобразить или скрыть дополнительные поля в зависимости от выбранного алгоритма
        self.algorithm_select(None)


    def algorithm_select(self, event):
        """
        Выбор алгоритма, отображение и скрытие дополнительных полей
        """
        algorithm = self.algorithm_combobox.get()
        if algorithm == "DBSCAN":
            self.hide_isolation_forest_fields()
            self.show_dbscan_fields()
            self.hide_hierarchical_fields()
            self.hide_decision_fields()
            self.hide_random_forest_fields()
        elif algorithm == "Изоляционный лес":
            self.show_isolation_forest_fields()
            self.hide_dbscan_fields()
            self.hide_hierarchical_fields()
            self.hide_decision_fields()
            self.hide_random_forest_fields()
        elif algorithm == "Иерархическая кластеризация":
            self.hide_isolation_forest_fields()
            self.hide_dbscan_fields()
            self.show_hierarchical_fields()
            self.hide_decision_fields()
            self.hide_random_forest_fields()
            self.load_model_combobox()
        elif algorithm == "Дерево решений":
            self.hide_isolation_forest_fields()
            self.hide_dbscan_fields()
            self.hide_hierarchical_fields()
            self.hide_random_forest_fields()
            self.show_decision_fields()
            self.load_model_combobox()
        elif algorithm == "Случайный лес":
            self.hide_isolation_forest_fields()
            self.hide_dbscan_fields()
            self.hide_hierarchical_fields()
            self.hide_decision_fields()
            self.show_random_forest_fields()
            self.load_model_combobox()


    def show_dbscan_fields(self):
        """
        Отображение дополнительных полей алгоритма DBSCAN
        """
        self.dbscan_eps_label.grid(row=0, column=0, padx=10, pady=15, sticky="w")
        self.dbscan_eps_entry.grid(row=0, column=1, padx=10, pady=15, sticky="w")
        self.dbscan_min_samples_label.grid(row=1, column=0, padx=10, pady=15, sticky="w")
        self.dbscan_min_samples_entry.grid(row=1, column=1, padx=10, pady=15, sticky="w")

    def hide_dbscan_fields(self):
        """
        Удаление дополнительных полей алгоритма DBSCAN
        """
        self.dbscan_eps_label.grid_remove()
        self.dbscan_eps_entry.grid_remove()
        self.dbscan_min_samples_label.grid_remove()
        self.dbscan_min_samples_entry.grid_remove()

    def show_hierarchical_fields(self):
        """
        Отображение дополнительных полей алгоритма иерархической кластеризации
        """
        self.hierarchical_linkage_label.grid(row=0, column=0, padx=10, pady=15, sticky="w")
        self.hierarchical_linkage_combobox.grid(row=0, column=1, padx=10, pady=15, sticky="w")

    def hide_hierarchical_fields(self):
        """
        Удаление дополнительных полей алгоритма иерархической кластеризации
        """
        self.hierarchical_linkage_label.grid_remove()
        self.hierarchical_linkage_combobox.grid_remove()

    def show_isolation_forest_fields(self):
        """
        Отображение дополнительных полей алгоритма изоляционного леса
        """
        self.model_label_if.grid(row=0, column=0, padx=10, pady=15, sticky="w")
        self.model_combobox_if.grid(row=0, column=1, padx=10, pady=15, sticky="w")

    def hide_isolation_forest_fields(self):
        """
        Удаление дополнительных полей алгоритма изоляционного леса
        """
        self.model_label_if.grid_remove()
        self.model_combobox_if.grid_remove()

    def show_decision_fields(self):
        """
        Отображение дополнительных полей алгоритма дерева решений
        """
        self.model_label_dt.grid(row=0, column=0, padx=10, pady=15, sticky="w")
        self.model_combobox_dt.grid(row=0, column=1, padx=10, pady=15, sticky="w")

    def hide_decision_fields(self):
        """
        Удаление дополнительных полей алгоритма дерева решений
        """
        self.model_label_dt.grid_remove()
        self.model_combobox_dt.grid_remove()

    def show_random_forest_fields(self):
        """
        Отображение дополнительных полей алгоритма случайного леса
        """
        self.model_label_rf.grid(row=0, column=0, padx=10, pady=15, sticky="w")
        self.model_combobox_rf.grid(row=0, column=1, padx=10, pady=15, sticky="w")

    def hide_random_forest_fields(self):
        """
        Удаление дополнительных полей алгоритма случайного леса леса
        """
        self.model_label_rf.grid_remove()
        self.model_combobox_rf.grid_remove()


    def choose_folder(self):
        """
        Выбор папки для вывода результатов
        """
        folder = askdirectory()
        if folder:
            self.selected_folder_entry.config(state="normal")
            self.selected_folder_entry.delete(0, tk.END)
            self.selected_folder_entry.insert(0, folder)


    def load_dataset_combobox(self):
        """
        Загрузка наименований таблиц для комбобокса из базы данных
        """
        try:
            # Соединение с базой данных
            conn = sqlite3.connect("app_database.db")
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            conn.close()

            # Загрузка имен таблиц в комбобокс
            self.dataset_combobox["values"] = [table[0] for table in tables]
        except sqlite3.Error as e:
            messagebox.showerror("Ошибка", f"Ошибка при загрузке данных: {e}")


    def load_model_combobox(self, event=None):
        models_dir = "models"
        selected_algorithm = self.algorithm_combobox.get()
        
        if selected_algorithm == "Изоляционный лес":
            models = [f for f in os.listdir(models_dir) if f.startswith("isol_for")]    # Список моделей, начинающихся на isol_for
            self.model_combobox_if["values"] = models
            if models:
                self.model_combobox_if.set(models[0])
        elif selected_algorithm == "Дерево решений":
            models = [f for f in os.listdir(models_dir) if f.startswith("dec_tree")]    # Список моделей, начинающихся на dec_tree
            self.model_combobox_dt["values"] = models
            if models:
                self.model_combobox_dt.set(models[0])
        elif selected_algorithm == "Случайный лес":
            models = [f for f in os.listdir(models_dir) if f.startswith("rand_for")]    # Список моделей, начинающихся на rand_for
            self.model_combobox_rf["values"] = models
            if models:
                self.model_combobox_rf.set(models[0])
        else:
            models = []


    def find_fakes(self):
        """
        Вызов алгоритмов нахождения фиктивных аккаунтов
        """
        algorithm = self.algorithm_combobox.get()
        data = self.dataset_combobox.get()
        visualization = self.visualization_combobox.get()
        folder = self.selected_folder_entry.get()

        if data == "":
            messagebox.showwarning("Предупреждение", "Выберите данные.")
        elif folder == "":
            messagebox.showwarning("Предупреждение", "Выберите папку для сохранения результатов.")
        else:
            making_features(data)  # Создание таблицы с признаками
            if algorithm == "DBSCAN":
                eps = self.dbscan_eps_entry.get()
                min_samples = self.dbscan_min_samples_entry.get()

                # Проверка корректности ввода значений eps и min_samples
                try:
                    eps = float(eps)
                    min_samples = int(min_samples)
                except ValueError:
                    messagebox.showwarning("Предупреждение", "Eps должен быть числом, Min Samples — целым числом.")
                    return
                if eps <= 0 or min_samples <= 0:
                    messagebox.showwarning("Предупреждение", "Eps и Min Samples должны быть положительными.")
                    return

                messagebox.showinfo("Информация", "Процесс поиска фейков запущен.")
                DBSCAN.run_dbscan_algorithm(data, eps, min_samples, visualization, folder)  # Вызов алгоритма DBSCAN
                messagebox.showinfo("Информация", "Фейки найдены.")

            elif algorithm == "Изоляционный лес":
                messagebox.showinfo("Информация", "Процесс поиска фейков запущен.")
                model_if=self.model_combobox_if.get()
                isolation_forest.run_isolation_forest_algorithm(data, model_if, visualization, folder) # Вызов алгоритма леса изоляции
                messagebox.showinfo("Информация", "Фейки найдены.")

            elif algorithm == "Иерархическая кластеризация":
                messagebox.showinfo("Информация", "Процесс поиска фейков запущен.")
                linkage_method = self.hierarchical_linkage_combobox.get()
                hierarchical_clustering.run_hierarchical_clustering(data, linkage_method, visualization, folder)    # Вызов алгоритма иерархической кластеризации
                messagebox.showinfo("Информация", "Фейки найдены.")
            
            elif algorithm == "Дерево решений":
                messagebox.showinfo("Информация", "Процесс поиска фейков запущен.")
                model_dt = self.model_combobox_dt.get()
                decision_tree.run_decision_tree_algorithm(data, model_dt, visualization, folder)    # Вызов алгоритма дерева решений
                messagebox.showinfo("Информация", "Фейки найдены.")

            elif algorithm == "Случайный лес":
                messagebox.showinfo("Информация", "Процесс поиска фейков запущен.")
                model_rf = self.model_combobox_rf.get()
                random_forest.run_random_forest_algorithm(data, model_rf, visualization, folder)    # Вызов алгоритма случайного леса
                messagebox.showinfo("Информация", "Фейки найдены.")


if __name__ == "__main__":
    root = tk.Tk()
    app = FindFakesScreen(root)
    root.mainloop()
