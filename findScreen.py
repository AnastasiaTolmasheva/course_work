import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter.filedialog import askdirectory
import sqlite3
import DBSCAN
import isolation_forest
import hierarchical_clustering
from makingFeatures import create_features_database
from augmentation import balance_data


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
        self.algorithm_combobox = ttk.Combobox(input_frame, values=["Лес изоляции", "DBSCAN", "Иерархическая кластеризация"], state="readonly", width=25, font=("Helvetica", 14))
        self.algorithm_combobox.grid(row=0, column=1, padx=0, pady=15, sticky="ew")
        self.algorithm_combobox.bind("<<ComboboxSelected>>", self.algorithm_select)
        self.algorithm_combobox.set("Лес изоляции")  # Выбор алгоритма по умолчанию

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

        # Дополнительные поля для Леса изоляции: выбор объема тестовой выборки и кнопка для выполнения аугментации 
        self.augmentation_button = ttk.Button(extra_frame, text="Выполнить аугментацию", style='Second.TButton', command=self.perform_augmentation, width=25)
        self.percentage_label = ttk.Label(extra_frame, text="Тестовая выборка:", font=("Helvetica", 14))
        self.percentage_combobox = ttk.Combobox(extra_frame, values=["10%", "20%", "30%"], state="readonly", font=("Helvetica", 14), width=6)

        # Дополнительные поля для Иерархической кластеризации: выбор метода соединения
        self.hierarchical_linkage_label = ttk.Label(extra_frame, text="Метод соединения:", font=("Helvetica", 14))
        self.hierarchical_linkage_combobox = ttk.Combobox(extra_frame, values=["single", "complete", "average", "ward"], state="readonly", font=("Helvetica", 14), width=10)

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
        elif algorithm == "Лес изоляции":
            self.show_isolation_forest_fields()
            self.hide_dbscan_fields()
            self.hide_hierarchical_fields()
        elif algorithm == "Иерархическая кластеризация":
            self.hide_isolation_forest_fields()
            self.hide_dbscan_fields()
            self.show_hierarchical_fields()


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
        Отображение дополнительных полей алгоритма леса изоляции
        """
        self.percentage_label.grid(row=0, column=0, padx=10, pady=15, sticky="w")
        self.percentage_combobox.grid(row=0, column=1, padx=10, pady=15, sticky="w")
        self.augmentation_button.grid(row=1, column=0, columnspan=2, padx=10, pady=15, sticky="w")


    def hide_isolation_forest_fields(self):
        """
        Удаление дополнительных полей алгоритма леса изоляции
        """
        self.augmentation_button.grid_remove()
        self.percentage_label.grid_remove()
        self.percentage_combobox.grid_remove()


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


    def perform_augmentation(self):
        """
        Выполнение аугментации данных (балансировка до соотношения 50/50)
        """
        data = self.dataset_combobox.get()
        if data:
            # Аугментация данных, подключение функции balance_data из модуля augmentation
            fake_count_before, real_count_before, fake_count_after, real_count_after, augmentation_needed, augmented_table_name = balance_data(data, "app_database.db")

            # Отображение результатов аугментации
            self.load_dataset_combobox()
            self.dataset_combobox.set(augmented_table_name)
            self.display_balancing_results(fake_count_before, real_count_before, fake_count_after, real_count_after, augmentation_needed)
        else:
            messagebox.showwarning("Предупреждение", "Выберите датасет для аугментации")


    def display_balancing_results(self, fake_count_before, real_count_before, fake_count_after, real_count_after, augmentation_needed):
        """
        Отображает всплывающее окно с результатами аугментации данных
        """
        root = tk.Tk()  # Создаем основное окно для диалогового окна
        root.withdraw()

        if augmentation_needed:
            # Проверяем, что данные после аугментации не None
            if fake_count_after is not None and real_count_after is not None:
                total_count_before = fake_count_before + real_count_before
                total_count_after = fake_count_after + real_count_after
                message = (
                    f"Результаты до аугментации:\n"
                    f"- Фейковые аккаунты: {fake_count_before}\n"
                    f"- Настоящие аккаунты: {real_count_before}\n"
                    f"- Всего: {total_count_before}\n\n"
                    f"Результаты после аугментации:\n"
                    f"- Фейковые аккаунты: {fake_count_after}\n"
                    f"- Настоящие аккаунты: {real_count_after}\n"
                    f"- Всего: {total_count_after}"
                )
            else:
                message = "Ошибка: данные после аугментации отсутствуют"
        else:
            message = "Аугментация данных не требуется: фейковые и настоящие аккаунты уже сбалансированы"

        # Отображаем диалоговое окно с информацией
        messagebox.showinfo("Результаты аугментации", message)

        # Завершаем работу окна
        root.destroy()


    def find_fakes(self):
        """
        Вызов алгоритмов нахлждения фиктивных аккаунтов
        """
        algorithm = self.algorithm_combobox.get()
        data = self.dataset_combobox.get()
        visualization = self.visualization_combobox.get()
        folder = self.selected_folder_entry.get()

        if algorithm == "":
            messagebox.showwarning("Предупреждение", "Выберите алгоритм")
        elif data == "":
            messagebox.showwarning("Предупреждение", "Выберите данные")
        elif visualization == "":
            messagebox.showwarning("Предупреждение", "Выберите необходимость визуализации")
        elif folder == "":
            messagebox.showwarning("Предупреждение", "Выберите папку для сохранения результатов")
        else:
            create_features_database(data)  # Создание таблицы с признаками, вызов функции create_features_database из модуля makingFeatures
            if algorithm == "DBSCAN":
                eps = self.dbscan_eps_entry.get()
                min_samples = self.dbscan_min_samples_entry.get()

                # Проверка корректности ввода значений eps и min_samples
                try:
                    eps = float(eps)  # Конвертация в float
                    min_samples = int(min_samples)  # Конвертация в int
                except ValueError:
                    messagebox.showwarning("Предупреждение", "Eps должен быть числом, Min Samples — целым числом")
                    return
                if eps <= 0 or min_samples <= 0:
                    messagebox.showwarning("Предупреждение", "Eps и Min Samples должны быть положительными")
                    return

                DBSCAN.run_dbscan_algorithm(data, eps, min_samples, visualization, folder)  # Вызов алгоритма DBSCAN

            elif algorithm == "Лес изоляции":
                test_dataset = self.percentage_combobox.get()
                test_dataset_fraction = float(test_dataset.replace('%', '')) / 100  # Перевод процентов в дробь
                if test_dataset:
                    isolation_forest.run_isolation_forest_algorithm(data, test_dataset_fraction, visualization, folder) # Вызов алгоритма леса изоляции
                else:
                    messagebox.showwarning("Предупреждение", "Выберите объем тестовой выборки")

            elif algorithm == "Иерархическая кластеризация":
                linkage_method = self.hierarchical_linkage_combobox.get()
                if linkage_method:
                    hierarchical_clustering.run_hierarchical_clustering(data, linkage_method, visualization, folder)    # Вызов алгоритма иерархической кластеризации
                else:
                    messagebox.showwarning("Предупреждение", "Выберите метод соединения")


if __name__ == "__main__":
    root = tk.Tk()
    app = FindFakesScreen(root)
    root.mainloop()
