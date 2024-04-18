import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter.filedialog import askdirectory
import sqlite3
import algorithms
from makingFeatures import create_features_database
from augmentation import balance_data
from teaching import train_isolation_forest_model


class FindFakesScreen(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Настройка модели")
        self.geometry("900x470")
        self.resizable(False, False)

        style_first = ttk.Style()
        style_first.configure('Second.TButton', font=('Helvetica', 14))

        # Лейбл с названием окна
        title_label = ttk.Label(self, text="Настройка модели", font=("Helvetica", 18))
        title_label.pack(pady=30)

        # Основной контейнер для фреймов
        main_pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_pane.pack(expand=False, fill=tk.X, padx=10, pady=5)

        # Фрейм для размещения полей ввода
        input_frame = ttk.Frame(main_pane)
        main_pane.add(input_frame, weight=1)

        # Фрейм для размещения дополнительных полей
        extra_frame = ttk.Frame(main_pane)
        main_pane.add(extra_frame, weight=1)

        # Фрейм для размещения кнопки и лейбла под PanedWindow
        folder_frame = ttk.Frame(self)
        folder_frame.pack(fill="x", padx=10)

        button_frame = ttk.Frame(self)
        button_frame.pack(fill="x", padx=10, pady=50)

        # Поля для ввода алгоритма, данных, визуализации и выбора папки для вывода результата
        self.algorithm_label = ttk.Label(input_frame, text="Алгоритм:", font=("Helvetica", 14))
        self.algorithm_label.grid(row=0, column=0, padx=10, pady=15, sticky="w")

        self.algorithm_combobox = ttk.Combobox(input_frame, values=["Лес изоляции", "DBSCAN", "Иерархическая кластеризация"], state="readonly", width=25, font=("Helvetica", 14))
        self.algorithm_combobox.grid(row=0, column=1, padx=10, pady=15, sticky="ew")
        self.algorithm_combobox.bind("<<ComboboxSelected>>", self.on_algorithm_select)
        self.algorithm_combobox.set("Лес изоляции")  # Выбор алгоритма по умолчанию

        self.data_label = ttk.Label(input_frame, text="Данные:", font=("Helvetica", 14))
        self.data_label.grid(row=1, column=0, padx=10, pady=15, sticky="w")
        self.data_combobox = ttk.Combobox(input_frame, state="readonly", font=("Helvetica", 14))
        self.data_combobox.bind("<<ComboboxSelected>>", self.load_data_combobox())
        self.data_combobox.grid(row=1, column=1, padx=10, pady=15, sticky="ew")

        self.visualization_label = ttk.Label(input_frame, text="Визуализация:", font=("Helvetica", 14))
        self.visualization_label.grid(row=2, column=0, padx=10, pady=15, sticky="w")
        self.visualization_combobox = ttk.Combobox(input_frame, values=["Да", "Нет"], state="readonly", font=("Helvetica", 14))
        self.visualization_combobox.grid(row=2, column=1, padx=10, pady=15, sticky="ew")
        self.visualization_combobox.set("Да")  # Выбор варианта по умолчанию

        self.results_label = ttk.Label(folder_frame, text="Вывод результатов:", font=("Helvetica", 14))
        self.results_label.grid(row=0, column=0, padx=10, pady=15, sticky="w")
        self.selected_folder_entry = ttk.Entry(folder_frame, font=("Helvetica", 14), width=22)
        self.selected_folder_entry.grid(row=0, column=1, padx=10, pady=15, sticky="ew")
        self.select_folder_button = ttk.Button(folder_frame, text="Выбрать", style='Second.TButton', command=self.choose_directory)
        self.select_folder_button.grid(row=0, column=2, padx=14.5, pady=15, sticky="ew")

        self.find_fakes_button = ttk.Button(button_frame, text="Найти фейки", style='Second.TButton', command=self.find_fakes, width=20)
        self.find_fakes_button.pack()


        # Дополнительные поля для DBSCAN
        self.dbscan_eps_label = ttk.Label(extra_frame, text="Eps:", font=("Helvetica", 14))
        self.dbscan_eps_entry = ttk.Entry(extra_frame, font=("Helvetica", 14), width=15)

        self.dbscan_min_samples_label = ttk.Label(extra_frame, text="Min Samples:", font=("Helvetica", 14))
        self.dbscan_min_samples_entry = ttk.Entry(extra_frame, font=("Helvetica", 14), width=15)

        # Дополнительные поля для Изолированного леса
        self.isolation_forest_anomaly_label = ttk.Label(extra_frame, text="Доля аномалий:", font=("Helvetica", 14))
        self.isolation_forest_anomaly_entry = ttk.Entry(extra_frame, font=("Helvetica", 14))
        
        self.augmentation_button = ttk.Button(extra_frame, text="Выполнить аугментацию", style='Second.TButton', command=self.perform_augmentation_button_click)
        self.train_model_button = ttk.Button(extra_frame, text="Обучить модель", style='Second.TButton', command=self.train_model_button_click)

        # Дополнительные поля для Иерархической кластеризации
        self.hierarchical_linkage_label = ttk.Label(extra_frame, text="Метод соединения:", font=("Helvetica", 14))
        self.hierarchical_linkage_combobox = ttk.Combobox(extra_frame, values=["single", "complete", "average", "ward"], state="readonly", font=("Helvetica", 14), width=15)

        # Вызываем метод, чтобы отобразить или скрыть дополнительные поля в зависимости от выбранного алгоритма
        self.on_algorithm_select(None)

    def on_algorithm_select(self, event):
        algorithm = self.algorithm_combobox.get()
        if algorithm == "DBSCAN":
            self.hide_isolation_forest_fields()
            self.show_dbscan_fields()
            self.hide_hierarchical_fields()
        elif algorithm == "Лес изоляции":
            self.show_isolation_forest_fields()
            self.hide_dbscan_fields()
            self.hide_hierarchical_fields()
        elif algorithm == "Иерархическая кластеризация":
            self.hide_isolation_forest_fields()
            self.hide_dbscan_fields()
            self.show_hierarchical_fields()


    def show_dbscan_fields(self):
        self.dbscan_eps_label.grid(row=0, column=0, padx=10, pady=15, sticky="w")
        self.dbscan_eps_entry.grid(row=0, column=1, padx=10, pady=15, sticky="w")
        self.dbscan_min_samples_label.grid(row=1, column=0, padx=10, pady=15, sticky="w")
        self.dbscan_min_samples_entry.grid(row=1, column=1, padx=10, pady=15, sticky="w")

    def hide_dbscan_fields(self):
        self.dbscan_eps_label.grid_remove()
        self.dbscan_eps_entry.grid_remove()
        self.dbscan_min_samples_label.grid_remove()
        self.dbscan_min_samples_entry.grid_remove()

    def show_hierarchical_fields(self):
        self.hierarchical_linkage_label.grid(row=0, column=0, padx=10, pady=15, sticky="w")
        self.hierarchical_linkage_combobox.grid(row=0, column=1, padx=10, pady=15, sticky="w")

    def hide_hierarchical_fields(self):
        self.hierarchical_linkage_label.grid_remove()
        self.hierarchical_linkage_combobox.grid_remove()

    def show_isolation_forest_fields(self):
        self.isolation_forest_anomaly_label.grid(row=0, column=0, padx=10, pady=15, sticky="w")
        self.isolation_forest_anomaly_entry.grid(row=0, column=1, padx=10, pady=15, sticky="ew")
        self.augmentation_button.grid(row=1, column=0, columnspan=2, padx=10, pady=15, sticky="ew")
        self.train_model_button.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="ew")

    def hide_isolation_forest_fields(self):
        self.isolation_forest_anomaly_label.grid_remove()
        self.isolation_forest_anomaly_entry.grid_remove()
        self.augmentation_button.grid_remove()
        self.train_model_button.grid_remove()


    def choose_directory(self):
        directory = askdirectory()
        if directory:
            self.selected_folder_entry.config(state="normal")
            self.selected_folder_entry.delete(0, tk.END)
            self.selected_folder_entry.insert(0, directory)


    def load_data_combobox(self):
        """
        Загрузка данных для комбобокса из базы данных
        """
        try:
            conn = sqlite3.connect('app_database.db')
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            conn.close()

            # Загрузка имен таблиц в комбобокс
            self.data_combobox["values"] = [table[0] for table in tables]
        except sqlite3.Error as e:
            messagebox.showerror("Ошибка", f"Ошибка при загрузке данных: {e}")
    

    def perform_augmentation_button_click(self):
        data = self.data_combobox.get()
        if data:
            balance_data(data, 'app_database.db')
            self.load_data_combobox()
            messagebox.showinfo("Информация", "Аугментация выполнена успешно.")
        else:
            messagebox.showwarning("Предупреждение", "Выберите данные для аугментации.")


    def train_model_button_click(self):
        data = self.data_combobox.get()
        anomaly = self.isolation_forest_anomaly_entry.get()
        create_features_database(data)

        if data and anomaly:
            # Вызов функции для обучения модели из модуля algorithms
            train_isolation_forest_model(data, anomaly)
            messagebox.showinfo("Информация", "Модель обучена успешно.")
        else:
            messagebox.showwarning("Предупреждение", "Пожалуйста, заполните все поля.")


    def find_fakes(self):
        algorithm = self.algorithm_combobox.get()
        data = self.data_combobox.get()
        visualization = self.visualization_combobox.get()
        folder = self.selected_folder_entry.get()

        if algorithm == "":
            messagebox.showwarning("Предупреждение", "Выберите алгоритм.")
        elif data == "":
            messagebox.showwarning("Предупреждение", "Выберите данные.")
        elif visualization == "":
            messagebox.showwarning("Предупреждение", "Выберите необходимость визуализации.")
        elif folder == "Выбрать":
            messagebox.showwarning("Предупреждение", "Выберите папку для вывода результатов.")
        else:
            if algorithm == "DBSCAN":
                create_features_database(data)
                eps = self.dbscan_eps_entry.get()
                min_samples = self.dbscan_min_samples_entry.get()
                if eps and min_samples:
                    eps = float(eps)
                    min_samples = int(min_samples)
                    algorithms.run_dbscan_algorithm(data, eps, min_samples, visualization, folder)
                else:
                    messagebox.showwarning("Предупреждение", "Введите значения для Eps и Min Samples.")
            elif algorithm == "Изолированный лес":
                create_features_database(data)
                anomaly = self.isolation_forest_anomaly_entry.get()
                if anomaly:
                    anomaly = float(anomaly)
                    algorithms.run_isolation_forest_algorithm(data, anomaly, visualization, folder)
                else:
                    messagebox.showwarning("Предупреждение", "Введите значение для Доли аномалий.")
            elif algorithm == "Иерархическая кластеризация":
                create_features_database(data)
                linkage_method = self.hierarchical_linkage_combobox.get()
                if linkage_method:
                    algorithms.run_hierarchical_clustering(data, linkage_method, visualization, folder)
                else:
                    messagebox.showwarning("Предупреждение", "Выберите метод соединения и расстояние.")
            else:
                messagebox.showinfo("Сообщение", "Фейки найдены.")


if __name__ == "__main__":
    root = tk.Tk()
    app = FindFakesScreen(root)
    root.mainloop()
