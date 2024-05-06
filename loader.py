import csv
import sqlite3
from tkinter import messagebox
from tkinter import filedialog


def create_table(table_name, columns):
    """
    Функция создания таблицы
    """
    conn = sqlite3.connect("app_database.db")
    cursor = conn.cursor()
    sql_query = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)})"
    cursor.execute(sql_query)
    conn.commit()
    conn.close()


def loading():
    """
    Функция для загрузки файлов в базу данных
    """
    filename = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    table_name = filename.split("/")[-1].split('.')[0]  # Извлечение имени файла

    # Проверка, выбрал ли пользователь файл
    if not filename:
        return

    # Проверка наличия таблицы с таким же именем
    conn = sqlite3.connect("app_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    existing_tables = cursor.fetchall()
    conn.close()

    if (table_name,) in existing_tables:
        confirm = messagebox.askyesno("Подтверждение", f"Таблица с именем '{table_name}' уже существует. Хотите перезаписать её?")
        if not confirm:
            return

    with open(filename, "r", encoding="utf-8") as file:
        reader = csv.reader(file)
        columns = next(reader)  # Считываем первую строку CSV файла с заголовками
        columns_with_types = [f"{columns[0]} INTEGER PRIMARY KEY"] + [f"{column} TEXT" for column in columns[1:]]
        create_table(table_name, columns_with_types)  # Создаем таблицу с соответствующими столбцами

        # Удаляем данные, если они были
        conn = sqlite3.connect("app_database.db")
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {table_name};")
        conn.commit()
        conn.close()

        # Вставляем данные из CSV файла в базу данных
        conn = sqlite3.connect("app_database.db")
        cursor = conn.cursor()
        with open(filename, "r", encoding="utf-8") as file:
            reader = csv.reader(file)
            next(reader)  # Пропускаем первую строку с заголовками
            for row in reader:
                cursor.execute(f"INSERT OR REPLACE INTO {table_name} VALUES ({', '.join(['?'] * len(row))})", row)
            conn.commit()
            conn.close()
    
    if filename:
        messagebox.showinfo("Успешно", f"Файл {table_name}.csv успешно загружен и сохранен")
    else:
        messagebox.showinfo("Ошибка", f"Файл {table_name}.csv не был загружен в базу данных")
