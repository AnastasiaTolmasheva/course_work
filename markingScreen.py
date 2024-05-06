import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import tkinter.simpledialog as simpledialog
from tkinter import Entry, Button
import sqlite3


class MarkingScreen(tk.Toplevel):
    def __init__(self, master):
        """
        Инициализация экрана редактирования данных

        На входе:
        - master: главное окно приложения
        """
        super().__init__(master)
        self.protocol("WM_DELETE_WINDOW", self.confirm_cancel)  # Обработчик закрытия окна
        self.master = master  # Сохранение ссылки на главное окно, чтобы при закрытии этого его снова отобразить

        self.title("Редактор данных")
        self.geometry("1400x720")

        self.edit_window_open = False  # Переменная для отслеживания состояния окна редактирования ячейки
        self.data_changed = False  # Переменная для отслеживания изменений в данных
        self.create_widgets()

        # Стиль для кнопок
        style_first = ttk.Style()
        style_first.configure("Second.TButton", font=("Helvetica", 14), width=20)


    def create_widgets(self):
        """
        Создание виджетов на экране редактирования данных
        """
        # Основной фрейм
        marking_frame = ttk.Frame(self)
        marking_frame.pack(fill=tk.BOTH, expand=True)

        # Заголовок окна
        label = ttk.Label(marking_frame, text="Редактор данных", font=("Helvetica", 20))
        label.pack(pady=10)

        # Фрейм для выбора таблицы
        table_selection_frame = ttk.Frame(marking_frame)
        table_selection_frame.pack(side=tk.TOP, fill=tk.X, padx=20, pady=5)

        # Комбобокс для выбора таблицы для редактирования
        label_tables = ttk.Label(table_selection_frame, text="Таблица", font=("Helvetica", 14))
        label_tables.pack(side=tk.LEFT, padx=10, pady=10)
        self.table_selection = ttk.Combobox(table_selection_frame, state="readonly", width=25, font=("Helvetica", 14))
        self.table_selection.pack(side=tk.LEFT, pady=10, padx=(0, 10))
        self.table_selection.bind("<<ComboboxSelected>>", self.load_selected_table)

        # Фрейм для таблицы с данными и скроллерами
        table_frame = ttk.Frame(marking_frame)
        table_frame.pack(padx=20, pady=5, fill=tk.BOTH, expand=True)

        # Скроллер для вертикального прокручивания
        vert_scrollbar = ttk.Scrollbar(table_frame, orient="vertical")
        vert_scrollbar.pack(side="right", fill="y")

        # Скроллер для горизонтального прокручивания
        horiz_scrollbar = ttk.Scrollbar(table_frame, orient="horizontal")
        horiz_scrollbar.pack(side="bottom", fill="x")

        # Таблица с данными датасета
        self.data_table = ttk.Treeview(table_frame, yscrollcommand=vert_scrollbar.set, xscrollcommand=horiz_scrollbar.set, show="headings")
        self.data_table.bind("<Double-1>", self.on_double_click)
        self.data_table.pack(fill="both", expand=True)
        vert_scrollbar.config(command=self.data_table.yview)
        horiz_scrollbar.config(command=self.data_table.xview)

        # Кнопки для добавления и удаления строк и столбцов
        add_row_button = ttk.Button(marking_frame, text="Добавить строку", style="Second.TButton", command=self.add_row)
        add_row_button.pack(side=tk.LEFT, padx=10, pady=10)

        remove_row_button = ttk.Button(marking_frame, text="Удалить строку", style="Second.TButton", command=self.remove_row)
        remove_row_button.pack(side=tk.LEFT, padx=10, pady=10)

        add_column_button = ttk.Button(marking_frame, text="Добавить столбец", style="Second.TButton", command=self.add_column)
        add_column_button.pack(side=tk.LEFT, padx=10, pady=10)

        remove_column_button = ttk.Button(marking_frame, text="Удалить столбец", style="Second.TButton", command=self.remove_column)
        remove_column_button.pack(side=tk.LEFT, padx=10, pady=10)

        save_button = ttk.Button(marking_frame, text="Сохранить", style="Second.TButton", command=self.save_marking)
        save_button.pack(side=tk.RIGHT, padx=20, pady=10)

        # Отображение загруженных таблиц в выпадающем списке
        self.display_loaded_tables()


    def display_loaded_tables(self):
        """
        Отображение списка таблиц базы данных в комбобоксе
        """
        # Подключение к базе данных и извлечение наименований таблиц
        conn = sqlite3.connect("app_database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        conn.close()

        # Отображение списка таблиц в выпадающем списке приложения
        self.table_selection["values"] = [table[0] for table in tables]


    def show_main_screen(self):
        """
        Закрытие окна редактирования, отображение главного экрана
        """
        self.master.deiconify()  # Главное окно становится видимым
        self.destroy()


    def confirm_cancel(self):
        """
        Подтверждение отмены или сохранения изменений при закрытии окна
        """
        if self.data_changed:
            confirm = messagebox.askyesno("Подтверждение", "Вы внесли изменения в данные. Хотите сохранить их перед выходом?")
            if confirm:
                self.save_marking()
                self.show_main_screen()
                self.destroy()
            else:
                self.show_main_screen()
                self.destroy()
        else:
            self.show_main_screen()
            self.destroy()


    def save_marking(self):
        """
        Сохранение изменений датасета в базе данных приложения
        """
        selected_table = self.table_selection.get()   # Получение имени выбранной таблицы

        if selected_table:
            # Получение данных из TreeView
            data = []
            for child in self.data_table.get_children():
                data.append(tuple(self.data_table.item(child, "values")))
            # Подключение к базе данных
            conn = sqlite3.connect("app_database.db")
            cursor = conn.cursor()

            # Сохранение изменений
            try:
                # Удаление существующей таблицы для обновления данных
                cursor.execute(f"DROP TABLE IF EXISTS {selected_table}")

                # Создание новой таблицы с актуальными данными
                columns = [self.data_table.heading(col)["text"] for col in self.data_table["columns"]]
                cursor.execute(f"CREATE TABLE {selected_table} ({', '.join([f'{col} TEXT' for col in columns])})")
                # Вставка измененых данных
                for row in data:
                    cursor.execute(f"INSERT INTO {selected_table} VALUES ({', '.join(['?'] * len(row))})", row)
                conn.commit()
                messagebox.showinfo("Успешно", "Изменения успешно сохранены в базе данных")
            except sqlite3.Error as e:
                conn.rollback()
                messagebox.showerror("Ошибка", f"Произошла ошибка при сохранении данных: {str(e)}")
            finally:
                conn.close()
                self.data_changed = False  # Сброс флага изменений после сохранения (новых изменений нет)
        else:
            messagebox.showwarning("Предупреждение", "Не выбрана таблица для сохранения данных")


    def load_selected_table(self, event):
        """
        Загрузка выбранной таблицы
        """
        selected_table = self.table_selection.get()
        if selected_table:
            # Подключение к базе данных и извлечение данных выбранной таблицы
            conn = sqlite3.connect("app_database.db")
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM {selected_table}")
            data = cursor.fetchall()
            conn.close()

            # Очистка таблицы перед отображением новых данных
            for child in self.data_table.get_children():
                self.data_table.delete(child)

            # Отображение данных выбранной таблицы в Treeview
            if data:
                columns = [description[0] for description in cursor.description]
                self.data_table["columns"] = tuple(columns)
                for col in columns:
                    self.data_table.heading(col, text=col)
                for row in data:
                    self.data_table.insert("", "end", values=row)


    def on_double_click(self, event):
        """
        Обработка двойного клика по ячейке таблицы для редактирования значения
        """
        if not self.edit_window_open:  # Проверяем, открыто ли окно редактирования ячейки
            self.edit_window_open = True  # Устанавливаем флаг, что окно редактирования ячейки открыто
            
            # Настройки окна редактирования значения
            edit_window = tk.Toplevel(self)
            edit_window.title("Редактирование ячейки")
            edit_window.geometry("300x100")

            # Блокировка обработчика событий таблицы данных - невозможно вызвать новое окно редактирования ячейки при уже одном открытом
            self.data_table.unbind("<Double-1>")
            cell = self.data_table.identify("item", event.x, event.y)

            # Определение индекса колонки
            column_id = self.data_table.identify_column(event.x)
            column_index = int(column_id.split("#")[1]) if '#' in column_id else 0
            initial_value = self.data_table.item(cell, "values")[column_index - 1]

            # Виджет для редактирования значения
            entry = Entry(edit_window, width=50)
            entry.insert(0, initial_value)
            entry.pack(padx=20, pady=15)

            def save_value():
                """
                Сохранение измененного значения ячейки
                """
                value = entry.get() # Получение нового значения ячейки
                self.data_table.set(cell, column_id, value)
                edit_window.destroy()
                self.edit_window_open = False  # Сброс флага после закрытия окна редактирования (новых изменений нет)

                # Разблокировка обработчика событий таблицы для дальнейшего редактирования
                self.data_table.bind("<Double-1>", self.on_double_click)
                self.data_changed = True  # Устанавливаем флаг изменений данных - было произведено действие

            # Виджет кнопки для применения изменений
            save_button = Button(edit_window, text="Применить", command=save_value)
            save_button.pack(side="left", padx=20, pady=5)

            def cancel():
                """
                Отмена редактирования значения ячейки
                """
                edit_window.destroy()
                self.edit_window_open = False  # Сброс флага после закрытия окна редактирования

                # Разблокировка обработчика событий таблицы для дальнейшего редактирования
                self.data_table.bind("<Double-1>", self.on_double_click)

            edit_window.protocol("WM_DELETE_WINDOW", cancel)

            # Виджет кнопки для отмены изменений
            cancel_button = Button(edit_window, text="Отмена", command=cancel)
            cancel_button.pack(side="right", padx=20, pady=5)


    def add_row(self):
        """
        Добавление новой строки в таблицу
        """
        new_row = tuple("" for _ in range(len(self.data_table["columns"])))
        self.data_table.insert("", "end", values=new_row)
        self.data_changed = True  # Устанавливаем флаг изменений данных - было произведено действие


    def remove_row(self):
        """
        Удаление выбранных строк из таблицы
        """
        selected_rows = self.data_table.selection()
        for row in selected_rows:
            self.data_table.delete(row)
            self.data_changed = True  # Устанавливаем флаг изменений данных - было произведено действие


    def add_column(self):
        """
        Добавление нового столбца в таблицу
        """
        new_column = simpledialog.askstring("Добавить столбец", "Введите название нового столбца:")
        if new_column:
            current_columns = [self.data_table.heading(col)["text"] for col in self.data_table["columns"]]
            self.data_table["columns"] += (new_column,)
            self.data_table.heading(new_column, text=new_column)
            for child in self.data_table.get_children():
                self.data_table.set(child, new_column, "")
            for col_name in current_columns:
                self.data_table.heading(col_name, text=col_name)
            self.data_changed = True  # Устанавливаем флаг изменений данных - было произведено действие


    def remove_column(self):
        """
        Удаление выбранного столбца из таблицы
        """
        column_remove = simpledialog.askstring("Удалить столбец", "Введите название столбца, который хотите удалить:")
        if column_remove and column_remove in self.data_table["columns"]:
            column_index = self.data_table["columns"].index(column_remove)
            self.data_table.heading(column_remove, text="")
            columns = list(self.data_table["columns"])
            columns.remove(column_remove)
            self.data_table["columns"] = tuple(columns)
            for child in self.data_table.get_children():
                self.data_table.set(child, self.data_table["columns"][column_index], "")
            self.data_changed = True  # Устанавливаем флаг изменений данных - было произведено действие


if __name__ == "__main__":
    app = MarkingScreen(None)   # Создание экземпляра окна редактирования
    app.mainloop()
