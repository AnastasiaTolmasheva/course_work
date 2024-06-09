import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from loader import loading
from markingScreen import MarkingScreen
from findScreen import FindFakesScreen 


class MainScreen(tk.Tk):
    """
    Класс главного окна приложения для поиска фиктивных аккаунтов
    """

    def __init__(self):
        """
        Инициализация главного окна
        """
        super().__init__()

        self.title("Нахождение фиктивных аккаунтов")
        self.geometry("600x350")
        self.resizable(False, False)
        self.create_widgets()

    def create_widgets(self):
        """
        Создание виджетов главного окна
        """
        # Основной фрейм
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Заголовок окна
        label = ttk.Label(self.main_frame, text="Приложение для поиска фиктивных аккаунтов", font=("Helvetica", 18))
        label.pack(pady=20)

        # Фрейм с кнопками
        buttons_frame = ttk.Frame(self.main_frame)
        buttons_frame.pack(pady=20)

        # Стиль для кнопок
        style_main = ttk.Style()
        style_main.configure("Main.TButton", font=("Helvetica", 14))

        # Список кнопок
        buttons = [
            ("Загрузить данные", self.load_data),
            ("Отредактировать данные", self.open_marking_screen),
            ("Найти фейки", self.find_fakes)
        ]

        # Создание кнопок и размещение их на форме
        for i, (btn_text, btn_command) in enumerate(buttons):
            btn = ttk.Button(buttons_frame, text=btn_text, width=30, style="Main.TButton", command=btn_command)
            btn.pack(pady=5, padx=10, fill=tk.X)
            if i < len(buttons) - 1:  # Стрелка между кнопками
                arrow_label = ttk.Label(buttons_frame, text="↓", font=("Helvetica", 14))
                arrow_label.pack()

        # Подсказка для помощи пользователю
        help_button = ttk.Button(self.main_frame, text="?", width=2, command=self.open_help)
        help_button.pack(side=tk.RIGHT, padx=10, pady=10)


    def open_marking_screen(self):
        """
        Открытие экрана редактирования данных
        """
        self.withdraw()  # Скрыть главное окно
        self.marking_screen = MarkingScreen(self)  # Создать экран редактирования данных
        self.marking_screen.grab_set()


    def show_main_screen(self):
        """
        Показ главного окна
        """
        self.marking_screen.destroy()  # Уничтожить экран редактирования и разметки данных
        self.deiconify()  # Восстановить главное окно


    def load_data(self):
        """
        Загрузка данных
        """
        loading()  # Вызов функции загрузки данных из модуля loader


    def find_fakes(self):
        """
        Открытие экрана настроек и поиска фиктивных аккаунтов
        """
        self.withdraw()  # Скрыть главное окно
        self.marking_screen = FindFakesScreen(self)  # Создать экран настройки и поиска фиктивных аккаунтов
        self.marking_screen.protocol("WM_DELETE_WINDOW", self.show_main_screen)  # Обработка закрытия окна
        self.marking_screen.grab_set()


    def open_help(self):
        """
        Окно помощи исследователю
        """
        help_text = """Приложение для поиска фиктивных аккаунтов. \nСоздатель: Толмачева А., КЭ-303

        - "Загрузить данные": вы можете загрузить таблицы csv формата.
        - "Отредактировать данные": вы можете отредактировать загруженные данные.
        - "Найти фейки": вы можете настроить алгоритм нахождения фиктивных аккаунтов и запустить его.
        """
        messagebox.showinfo("Помощь", help_text)  # Показать окно с информацией


if __name__ == "__main__":
    app = MainScreen()  # Создание экземпляра главного окна
    app.mainloop()  # Запуск главного цикла программы
