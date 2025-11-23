import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import random
import threading
import time
from datetime import datetime, timedelta
import json
import csv
import sqlite3
import smtplib
from email.mime.text import*
from email.mime.multipart import*
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import deque
import logging
import os


class RadiationMonitoringSystem:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Система контроля уровня радиации - АО 'КОНСИСТ-ОС'")
        self.root.geometry("1400x900")

        # Конфигурация системы
        self.config = {
            'polling_interval': 5,  # секунды
            'warning_threshold': 1.0,  # мкЗв/ч
            'danger_threshold': 2.5,  # мкЗв/ч
            'smtp_server': 'smtp.company.com',
            'smtp_port': 587,
            'notification_email': 'safety@company.com',
            'notification_phone': '+79001234567'
        }

        # Хранилище данных
        self.historical_data = []
        self.alerts_log = deque(maxlen=1000)
        self.sensor_configs = {}
        self.emergency_contacts = []

        # Инициализация компонентов
        self.setup_logging()
        self.init_database()
        self.init_sensor_configs()
        self.init_contacts()
        self.setup_ui()
        self.start_data_collection()

    def setup_logging(self):
        """Настройка системы логирования"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('radiation_monitoring.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def init_database(self):
        """Инициализация базы данных"""
        try:
            self.conn = sqlite3.connect('radiation_monitoring.db', check_same_thread=False)
            self.create_tables()
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка инициализации БД: {e}")
            messagebox.showerror("Ошибка", f"Не удалось инициализировать базу данных: {e}")

    def create_tables(self):
        """Создание таблиц в базе данных"""
        cursor = self.conn.cursor()

        # Таблица датчиков
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sensors (
                sensor_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                location TEXT NOT NULL,
                threshold REAL DEFAULT 1.0,
                calibration_date TEXT,
                status TEXT DEFAULT 'active'
            )
        ''')

        # Таблица измерений
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sensor_id TEXT,
                radiation_level REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT,
                FOREIGN KEY (sensor_id) REFERENCES sensors (sensor_id)
            )
        ''')

        # Таблица оповещений
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sensor_id TEXT,
                alert_type TEXT,
                threshold_value REAL,
                actual_value REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                notified INTEGER DEFAULT 0,
                FOREIGN KEY (sensor_id) REFERENCES sensors (sensor_id)
            )
        ''')

        self.conn.commit()

    def init_sensor_configs(self):
        """Инициализация конфигурации датчиков"""
        self.sensor_configs = {
            "Д-124": {
                "name": "Датчик радиации А-1",
                "location": "Участок А-1",
                "threshold": 1.0,
                "calibration_date": "2024-01-15",
                "status": "active"
            },
            "Д-128": {
                "name": "Датчик радиации Б-3",
                "location": "Участок Б-3",
                "threshold": 1.0,
                "calibration_date": "2024-01-20",
                "status": "active"
            },
            "Д-135": {
                "name": "Датчик радиации В-2",
                "location": "Участок В-2",
                "threshold": 1.0,
                "calibration_date": "2024-01-18",
                "status": "active"
            },
            "Д-142": {
                "name": "Датчик радиации Г-4",
                "location": "Участок Г-4",
                "threshold": 1.0,
                "calibration_date": "2024-01-22",
                "status": "active"
            }
        }

        # Сохранение датчиков в БД
        cursor = self.conn.cursor()
        for sensor_id, config in self.sensor_configs.items():
            cursor.execute('''
                INSERT OR REPLACE INTO sensors (sensor_id, name, location, threshold, calibration_date, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (sensor_id, config['name'], config['location'], config['threshold'],
                  config['calibration_date'], config['status']))
        self.conn.commit()

    def init_contacts(self):
        """Инициализация списка контактов для оповещений"""
        self.emergency_contacts = [
            "Главный инженер: +79001112233",
            "Начальник смены: +79004445566",
            "Радиационная безопасность: safety@company.com",
            "Технический отдел: tech@company.com",
            "Служба эксплуатации: +79007778899"
        ]

    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        # Создаем панель с вкладками
        self.tab_control = ttk.Notebook(self.root)

        # Создаем вкладки
        self.dashboard_tab = ttk.Frame(self.tab_control)
        self.sensors_tab = ttk.Frame(self.tab_control)
        self.data_collection_tab = ttk.Frame(self.tab_control)
        self.notifications_tab = ttk.Frame(self.tab_control)
        self.reports_tab = ttk.Frame(self.tab_control)
        self.settings_tab = ttk.Frame(self.tab_control)

        # Добавляем вкладки
        self.tab_control.add(self.dashboard_tab, text="📊 Панель управления")
        self.tab_control.add(self.sensors_tab, text="📡 Датчики")
        self.tab_control.add(self.data_collection_tab, text="🔍 Сбор данных")
        self.tab_control.add(self.notifications_tab, text="🔔 Уведомления")
        self.tab_control.add(self.reports_tab, text="📋 Отчеты")
        self.tab_control.add(self.settings_tab, text="⚙️ Настройки")

        self.tab_control.pack(expand=1, fill="both")

        # Инициализация панелей
        self.create_dashboard_panel()
        self.create_sensors_panel()
        self.create_data_collection_panel()
        self.create_notifications_panel()
        self.create_reports_panel()
        self.create_settings_panel()

    def create_dashboard_panel(self):
        """Создание панели управления"""
        # Основной фрейм
        main_frame = ttk.Frame(self.dashboard_tab)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Заголовок
        title_label = ttk.Label(main_frame,
                                text="СИСТЕМА КОНТРОЛЯ УРОВНЯ РАДИАЦИИ",
                                font=("Arial", 16, "bold"))
        title_label.pack(pady=10)

        # Фрейм для карточек датчиков
        cards_frame = ttk.Frame(main_frame)
        cards_frame.pack(fill="both", expand=True)

        # Создаем карточки датчиков
        self.sensor_cards = {}
        sensors_list = list(self.sensor_configs.keys())

        for i, sensor_id in enumerate(sensors_list):
            row = i // 2
            col = i % 2

            card = ttk.LabelFrame(cards_frame, text=self.sensor_configs[sensor_id]["location"], padding=10)
            card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

            # ID датчика
            sensor_label = ttk.Label(card, text=f"Датчик: {sensor_id}", font=("Arial", 10, "bold"))
            sensor_label.pack(pady=2)

            # Наименование
            name_label = ttk.Label(card, text=self.sensor_configs[sensor_id]["name"])
            name_label.pack(pady=2)

            # Значение (будет обновляться)
            value_label = ttk.Label(card, text="0.00 мкЗв/ч", font=("Arial", 16, "bold"))
            value_label.pack(pady=5)

            # Статус (будет обновляться)
            status_label = ttk.Label(card, text="Норма", font=("Arial", 10, "bold"))
            status_label.pack()

            # Индикатор уровня
            level_frame = ttk.Frame(card, height=20)
            level_frame.pack(fill="x", pady=5)
            level_frame.pack_propagate(False)

            level_indicator = ttk.Label(level_frame, background="green")
            level_indicator.pack(fill="both")

            # Футер с временем обновления
            footer_label = ttk.Label(card, text="Обновлено: --:--:--",
                                     font=("Arial", 8), foreground="gray")
            footer_label.pack(pady=2)

            # Сохраняем элементы для обновления
            self.sensor_cards[sensor_id] = {
                "card": card,
                "value_label": value_label,
                "status_label": status_label,
                "level_indicator": level_indicator,
                "footer_label": footer_label
            }

        # Настройка весов для растягивания
        for i in range(2):
            cards_frame.grid_columnconfigure(i, weight=1)
            cards_frame.grid_rowconfigure(i, weight=1)

        # Панель управления
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill="x", pady=10)

        ttk.Button(control_frame, text="Обновить данные",
                   command=self.manual_data_collection).pack(side="left", padx=5)
        ttk.Button(control_frame, text="Сброс аварийных сигналов",
                   command=self.reset_alarms).pack(side="left", padx=5)
        ttk.Button(control_frame, text="Тест оповещения",
                   command=self.send_test_notification).pack(side="left", padx=5)

        # График в реальном времени
        self.setup_realtime_chart(main_frame)

    def setup_realtime_chart(self, parent):
        """Настройка графика в реальном времени"""
        chart_frame = ttk.LabelFrame(parent, text="График уровня радиации в реальном времени", padding=10)
        chart_frame.pack(fill="x", pady=10)

        # Создаем фигуру для matplotlib
        self.fig, self.ax = plt.subplots(figsize=(10, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, chart_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # Инициализация данных для графика
        self.chart_data = {sensor_id: deque(maxlen=50) for sensor_id in self.sensor_configs.keys()}
        self.chart_timestamps = deque(maxlen=50)

        # Настройка графика
        self.ax.set_xlabel('Время')
        self.ax.set_ylabel('Уровень радиации (мкЗв/ч)')
        self.ax.set_title('Динамика уровня радиации по датчикам')
        self.ax.grid(True, alpha=0.3)

        self.lines = {}
        colors = ['blue', 'red', 'green', 'orange']
        for i, sensor_id in enumerate(self.sensor_configs.keys()):
            line, = self.ax.plot([], [], label=sensor_id, color=colors[i % len(colors)], linewidth=2)
            self.lines[sensor_id] = line

        self.ax.legend(loc='upper left')

    def update_chart(self):
        """Обновление графика"""
        if hasattr(self, 'lines') and self.lines:
            try:
                for sensor_id in self.sensor_configs.keys():
                    if sensor_id in self.chart_data and len(self.chart_data[sensor_id]) > 0:
                        # Обновляем данные линии
                        self.lines[sensor_id].set_data(
                            range(len(self.chart_data[sensor_id])),
                            list(self.chart_data[sensor_id])
                        )

                # Автоматическое масштабирование
                if any(len(data) > 0 for data in self.chart_data.values()):
                    self.ax.relim()
                    self.ax.autoscale_view()
                    self.canvas.draw_idle()  # Используем draw_idle вместо draw
            except Exception as e:
                self.logger.error(f"Ошибка обновления графика: {e}")

    def create_sensors_panel(self):
        """Создание панели датчиков"""
        main_frame = ttk.Frame(self.sensors_tab)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Таблица датчиков
        columns = ("ID датчика", "Наименование", "Участок", "Порог", "Калибровка", "Статус")
        self.sensors_tree = ttk.Treeview(main_frame, columns=columns, show="headings", height=15)

        # Настройка колонок
        column_widths = [120, 200, 150, 80, 120, 100]
        for col, width in zip(columns, column_widths):
            self.sensors_tree.heading(col, text=col)
            self.sensors_tree.column(col, width=width)

        # Заполнение данными
        for sensor_id, config in self.sensor_configs.items():
            self.sensors_tree.insert("", "end", values=(
                sensor_id,
                config["name"],
                config["location"],
                f"{config['threshold']} мкЗв/ч",
                config["calibration_date"],
                config["status"]
            ))

        self.sensors_tree.pack(fill="both", expand=True)

        # Панель кнопок
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=10)

        ttk.Button(button_frame, text="Добавить датчик",
                   command=self.show_add_sensor_dialog).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Редактировать",
                   command=self.show_edit_sensor_dialog).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Калибровка",
                   command=self.show_calibration_dialog).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Обновить",
                   command=self.refresh_sensors_table).pack(side="left", padx=5)

    def create_data_collection_panel(self):
        """Создание панели сбора данных"""
        main_frame = ttk.Frame(self.data_collection_tab)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Статистика сбора данных
        stats_frame = ttk.LabelFrame(main_frame, text="Статистика сбора данных", padding=10)
        stats_frame.pack(fill="x", pady=5)

        stats_grid = ttk.Frame(stats_frame)
        stats_grid.pack(fill="x")

        self.stats_labels = {}
        stats_info = [
            ("Всего измерений:", "0"),
            ("За сегодня:", "0"),
            ("Превышений порога:", "0"),
            ("Последнее обновление:", "--:--:--"),
            ("Активных датчиков:", str(len(self.sensor_configs))),
            ("Статус системы:", "✅ Активна")
        ]

        for i, (label, value) in enumerate(stats_info):
            row = i // 3
            col = (i % 3) * 2

            ttk.Label(stats_grid, text=label, font=("Arial", 9)).grid(row=row, column=col, sticky="w", padx=5, pady=2)
            value_label = ttk.Label(stats_grid, text=value, font=("Arial", 9, "bold"))
            value_label.grid(row=row, column=col + 1, sticky="w", padx=5, pady=2)
            self.stats_labels[label] = value_label

        # Журнал измерений
        log_frame = ttk.LabelFrame(main_frame, text="Журнал последних измерений", padding=10)
        log_frame.pack(fill="both", expand=True, pady=5)

        columns = ("Время", "Датчик", "Участок", "Уровень радиации", "Статус")
        self.data_tree = ttk.Treeview(log_frame, columns=columns, show="headings", height=15)

        column_widths = [150, 100, 120, 120, 100]
        for col, width in zip(columns, column_widths):
            self.data_tree.heading(col, text=col)
            self.data_tree.column(col, width=width)

        self.data_tree.pack(fill="both", expand=True)

        # Загрузка последних записей
        self.load_recent_measurements()

    def create_notifications_panel(self):
        """Создание панели уведомлений"""
        main_frame = ttk.Frame(self.notifications_tab)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Настройки оповещений
        settings_frame = ttk.LabelFrame(main_frame, text="Настройки оповещений", padding=10)
        settings_frame.pack(fill="x", pady=5)

        # Пороговые значения
        threshold_frame = ttk.Frame(settings_frame)
        threshold_frame.pack(fill="x", pady=5)

        ttk.Label(threshold_frame, text="Порог предупреждения:").pack(side="left", padx=5)
        self.warning_threshold_var = tk.StringVar(value=str(self.config['warning_threshold']))
        warning_entry = ttk.Entry(threshold_frame, textvariable=self.warning_threshold_var, width=10)
        warning_entry.pack(side="left", padx=5)
        ttk.Label(threshold_frame, text="мкЗв/ч").pack(side="left", padx=5)

        ttk.Label(threshold_frame, text="Порог опасности:").pack(side="left", padx=5)
        self.danger_threshold_var = tk.StringVar(value=str(self.config['danger_threshold']))
        danger_entry = ttk.Entry(threshold_frame, textvariable=self.danger_threshold_var, width=10)
        danger_entry.pack(side="left", padx=5)
        ttk.Label(threshold_frame, text="мкЗв/ч").pack(side="left", padx=5)

        # Контакты для оповещений
        contacts_frame = ttk.LabelFrame(settings_frame, text="Контакты для оповещений", padding=10)
        contacts_frame.pack(fill="x", pady=5)

        self.contacts_text = tk.Text(contacts_frame, height=4, width=60)
        self.contacts_text.pack(fill="x", padx=5, pady=5)

        for contact in self.emergency_contacts:
            self.contacts_text.insert("end", contact + "\n")

        # Журнал оповещений
        alerts_frame = ttk.LabelFrame(main_frame, text="Журнал оповещений", padding=10)
        alerts_frame.pack(fill="both", expand=True, pady=5)

        columns = ("Время", "Датчик", "Тип", "Уровень", "Порог", "Статус")
        self.alerts_tree = ttk.Treeview(alerts_frame, columns=columns, show="headings", height=15)

        column_widths = [150, 100, 100, 100, 100, 100]
        for col, width in zip(columns, column_widths):
            self.alerts_tree.heading(col, text=col)
            self.alerts_tree.column(col, width=width)

        self.alerts_tree.pack(fill="both", expand=True)

        # Кнопки управления
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=10)

        ttk.Button(button_frame, text="Сохранить настройки",
                   command=self.save_notification_settings).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Тест оповещения",
                   command=self.send_test_notification).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Очистить журнал",
                   command=self.clear_alerts_log).pack(side="left", padx=5)

    def create_reports_panel(self):
        """Создание панели отчетов"""
        main_frame = ttk.Frame(self.reports_tab)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Панель формирования отчетов
        reports_frame = ttk.LabelFrame(main_frame, text="Формирование отчетов", padding=10)
        reports_frame.pack(fill="x", pady=5)

        # Кнопки отчетов
        reports_grid = ttk.Frame(reports_frame)
        reports_grid.pack(fill="x")

        report_types = [
            ("Суточный отчет (CSV)", self.generate_daily_report),
            ("Недельный отчет (CSV)", self.generate_weekly_report),
            ("Месячный отчет (CSV)", self.generate_monthly_report),
            ("Статистический отчет", self.generate_statistical_report),
            ("Отчет по событиям", self.generate_events_report),
            ("Экспорт всех данных", self.export_all_data)
        ]

        for i, (text, command) in enumerate(report_types):
            row = i // 3
            col = i % 3
            btn = ttk.Button(reports_grid, text=text, command=command)
            btn.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
            reports_grid.columnconfigure(col, weight=1)

        # Статистика базы данных
        stats_frame = ttk.LabelFrame(main_frame, text="Статистика базы данных", padding=10)
        stats_frame.pack(fill="x", pady=5)

        self.db_stats_labels = {}
        db_stats = [
            ("Всего записей:", "0"),
            ("Размер БД:", "0 МБ"),
            ("Первая запись:", "--"),
            ("Последняя запись:", "--")
        ]

        stats_grid = ttk.Frame(stats_frame)
        stats_grid.pack(fill="x")

        for i, (label, value) in enumerate(db_stats):
            ttk.Label(stats_grid, text=label).grid(row=0, column=i * 2, sticky="w", padx=5, pady=2)
            value_label = ttk.Label(stats_grid, text=value)
            value_label.grid(row=0, column=i * 2 + 1, sticky="w", padx=5, pady=2)
            self.db_stats_labels[label] = value_label

        # Обновление статистики
        self.update_db_statistics()

    def create_settings_panel(self):
        """Создание панели настроек"""
        main_frame = ttk.Frame(self.settings_tab)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Основные настройки
        settings_frame = ttk.LabelFrame(main_frame, text="Основные настройки системы", padding=10)
        settings_frame.pack(fill="x", pady=10)

        settings_data = [
            ("Интервал опроса датчиков (сек):", "polling_interval", "5"),
            ("Порог предупреждения (мкЗв/ч):", "warning_threshold", "1.0"),
            ("Порог опасности (мкЗв/ч):", "danger_threshold", "2.5"),
            ("SMTP сервер:", "smtp_server", "smtp.company.com"),
            ("Порт SMTP:", "smtp_port", "587"),
            ("Email для уведомлений:", "notification_email", "safety@company.com")
        ]

        self.settings_entries = {}

        for i, (label, key, default) in enumerate(settings_data):
            frame = ttk.Frame(settings_frame)
            frame.pack(fill="x", pady=5)

            ttk.Label(frame, text=label, width=25).pack(side="left")
            entry = ttk.Entry(frame)
            entry.insert(0, str(self.config.get(key, default)))
            entry.pack(side="right", fill="x", expand=True, padx=10)

            self.settings_entries[key] = entry

        # Кнопки управления
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=20)

        ttk.Button(button_frame, text="Сохранить настройки",
                   command=self.save_settings).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Сброс к умолчаниям",
                   command=self.reset_settings).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Резервное копирование",
                   command=self.create_backup).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Восстановление",
                   command=self.restore_backup).pack(side="left", padx=5)

    def start_data_collection(self):
        """Запуск сбора данных"""
        self.data_collection_active = True
        self.collection_thread = threading.Thread(target=self.data_collection_worker, daemon=True)
        self.collection_thread.start()
        self.logger.info("Система сбора данных запущена")

    def data_collection_worker(self):
        """Рабочий поток для сбора данных"""
        while self.data_collection_active:
            try:
                self.collect_sensor_data()
                time.sleep(self.config['polling_interval'])
            except Exception as e:
                self.logger.error(f"Ошибка в потоке сбора данных: {e}")
                time.sleep(5)  # Пауза при ошибке

    def collect_sensor_data(self):
        """Сбор данных с датчиков"""
        sensors = list(self.sensor_configs.keys())
        locations = [self.sensor_configs[sensor_id]["location"] for sensor_id in sensors]

        for i, sensor_id in enumerate(sensors):
            try:
                # Имитация чтения данных с датчика
                base_value = 0.1 + (i * 0.3)
                variation = random.uniform(-0.1, 0.1)
                radiation = max(0.01, base_value + variation)

                # Имитация случайных аномалий (10% вероятность)
                if random.random() < 0.1:
                    radiation *= random.uniform(1.5, 4.0)

                # Определение статуса
                status = self.determine_status(radiation)

                # Сохранение данных
                self.store_measurement(sensor_id, radiation, status, locations[i])

                # Обновление интерфейса
                self.root.after(0, lambda sid=sensor_id, r=radiation, s=status:
                self.update_sensor_display(sid, r, s))

                # Проверка пороговых значений
                self.check_thresholds(sensor_id, radiation, status)

            except Exception as e:
                self.logger.error(f"Ошибка сбора данных с датчика {sensor_id}: {e}")

        # Обновление статистики
        self.root.after(0, self.update_statistics)
        self.root.after(0, self.update_chart)

    def determine_status(self, radiation_level):
        """Определение статуса по уровню радиации"""
        if radiation_level >= self.config['danger_threshold']:
            return "ОПАСНО"
        elif radiation_level >= self.config['warning_threshold']:
            return "ПРЕДУПРЕЖДЕНИЕ"
        else:
            return "НОРМА"

    def store_measurement(self, sensor_id, radiation_level, status, location):
        """Сохранение измерения в базу данных"""
        try:
            cursor = self.conn.cursor()
            timestamp = datetime.now()

            cursor.execute('''
                INSERT INTO measurements (sensor_id, radiation_level, timestamp, status)
                VALUES (?, ?, ?, ?)
            ''', (sensor_id, radiation_level, timestamp, status))

            self.conn.commit()

            # Добавление в исторические данные для отображения
            measurement_data = {
                'timestamp': timestamp,
                'sensor_id': sensor_id,
                'value': radiation_level,
                'status': status,
                'location': location
            }
            self.historical_data.append(measurement_data)

            # Ограничение размера исторических данных в памяти
            if len(self.historical_data) > 1000:
                self.historical_data.pop(0)

            # Обновление данных для графика
            if sensor_id not in self.chart_data:
                self.chart_data[sensor_id] = deque(maxlen=50)
            self.chart_data[sensor_id].append(radiation_level)

            self.logger.debug(f"Сохранено измерение: {sensor_id} - {radiation_level:.2f} мкЗв/ч")

        except sqlite3.Error as e:
            self.logger.error(f"Ошибка сохранения в БД: {e}")

    def update_sensor_display(self, sensor_id, radiation, status):
        """Обновление отображения данных датчика"""
        if sensor_id in self.sensor_cards:
            card_data = self.sensor_cards[sensor_id]

            # Определение цвета в зависимости от статуса
            if status == "ОПАСНО":
                color = "red"
            elif status == "ПРЕДУПРЕЖДЕНИЕ":
                color = "orange"
            else:
                color = "green"

            # Обновление значений
            card_data["value_label"].config(text=f"{radiation:.2f} мкЗв/ч")
            card_data["status_label"].config(text=status, foreground=color)
            card_data["level_indicator"].config(background=color)
            card_data["footer_label"].config(text=f"Обновлено: {datetime.now().strftime('%H:%M:%S')}")

    def check_thresholds(self, sensor_id, radiation_level, status):
        """Проверка превышения пороговых значений"""
        try:
            if status in ["ПРЕДУПРЕЖДЕНИЕ", "ОПАСНО"]:
                cursor = self.conn.cursor()
                timestamp = datetime.now()

                # Определение типа оповещения
                if status == "ОПАСНО":
                    alert_type = "CRITICAL"
                    threshold = self.config['danger_threshold']
                    self.send_emergency_notification(sensor_id, radiation_level, threshold)
                else:
                    alert_type = "WARNING"
                    threshold = self.config['warning_threshold']
                    self.send_warning_notification(sensor_id, radiation_level, threshold)

                # Запись в журнал оповещений
                cursor.execute('''
                    INSERT INTO alerts (sensor_id, alert_type, threshold_value, actual_value, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                ''', (sensor_id, alert_type, threshold, radiation_level, timestamp))

                self.conn.commit()

                # Обновление интерфейса
                self.root.after(0, self.update_alerts_tree)

                self.logger.warning(f"Превышение порога: {sensor_id} - {radiation_level:.2f} мкЗв/ч")

        except Exception as e:
            self.logger.error(f"Ошибка проверки порогов: {e}")

    def send_emergency_notification(self, sensor_id, radiation_level, threshold):
        """Отправка аварийного уведомления"""
        subject = f"🚨 КРИТИЧЕСКОЕ ПРЕВЫШЕНИЕ! Датчик {sensor_id}"
        message = f"""
        ВНИМАНИЕ! КРИТИЧЕСКОЕ ПРЕВЫШЕНИЕ УРОВНЯ РАДИАЦИИ!

        Детали:
        - Датчик: {sensor_id}
        - Местоположение: {self.sensor_configs[sensor_id]['location']}
        - Текущий уровень: {radiation_level:.2f} мкЗв/ч
        - Пороговое значение: {threshold} мкЗв/ч
        - Время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}

        НЕОБХОДИМО НЕМЕДЛЕННО ПРИНЯТЬ МЕРЫ!
        """

        self.send_email_notification(subject, message)
        self.logger.critical(f"Отправлено аварийное уведомление: {sensor_id}")

    def send_warning_notification(self, sensor_id, radiation_level, threshold):
        """Отправка предупреждения"""
        subject = f"⚠️ ПРЕДУПРЕЖДЕНИЕ: Превышение уровня радиации - {sensor_id}"
        message = f"""
        ПРЕДУПРЕЖДЕНИЕ: Превышение уровня радиации

        Детали:
        - Датчик: {sensor_id}
        - Местоположение: {self.sensor_configs[sensor_id]['location']}
        - Текущий уровень: {radiation_level:.2f} мкЗв/ч
        - Пороговое значение: {threshold} мкЗв/ч
        - Время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}

        Рекомендуется проверить оборудование и принять меры.
        """

        self.send_email_notification(subject, message)
        self.logger.warning(f"Отправлено предупреждение: {sensor_id}")

    def send_email_notification(self, subject, message):
        """Отправка email уведомления"""
        try:
            # В реальной системе здесь будет код для отправки email
            # Для демонстрации просто логируем
            self.logger.info(f"EMAIL УВЕДОМЛЕНИЕ: {subject}")
            self.logger.info(f"Сообщение: {message.strip()}")

            # Имитация отправки (в реальной системе раскомментировать)
            """
            msg = MimeMultipart()
            msg['From'] = self.config['notification_email']
            msg['To'] = self.config['notification_email']
            msg['Subject'] = subject

            msg.attach(MimeText(message, 'plain'))

            server = smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port'])
            server.starttls()
            # server.login(username, password)  # Добавить учетные данные
            server.send_message(msg)
            server.quit()
            """

        except Exception as e:
            self.logger.error(f"Ошибка отправки email: {e}")

    def send_test_notification(self):
        """Отправка тестового уведомления"""
        self.send_email_notification(
            "Тестовое уведомление - Система контроля радиации",
            "Это тестовое уведомление от системы контроля уровня радиации.\n\nСистема работает нормально."
        )
        messagebox.showinfo("Тест", "Тестовое уведомление отправлено!")

    # Методы для работы с отчетами
    def generate_daily_report(self):
        """Генерация суточного отчета"""
        try:
            cursor = self.conn.cursor()
            today = datetime.now().date()

            cursor.execute('''
                SELECT sensor_id, AVG(radiation_level), MAX(radiation_level), MIN(radiation_level), COUNT(*)
                FROM measurements 
                WHERE DATE(timestamp) = ?
                GROUP BY sensor_id
            ''', (today,))

            results = cursor.fetchall()

            filename = f"radiation_daily_report_{today.strftime('%Y%m%d')}.csv"

            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Суточный отчет по уровню радиации', f"Дата: {today}"])
                writer.writerow([])
                writer.writerow(['Датчик', 'Средний уровень', 'Максимум', 'Минимум', 'Измерений'])

                for row in results:
                    writer.writerow([
                        row[0],
                        f"{row[1]:.2f} мкЗв/ч",
                        f"{row[2]:.2f} мкЗв/ч",
                        f"{row[3]:.2f} мкЗв/ч",
                        row[4]
                    ])

            messagebox.showinfo("Успех", f"Суточный отчет создан:\n{filename}")
            self.logger.info(f"Создан суточный отчет: {filename}")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать отчет: {e}")
            self.logger.error(f"Ошибка создания отчета: {e}")

    def generate_weekly_report(self):
        """Генерация недельного отчета"""
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=7)

            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT sensor_id, AVG(radiation_level), MAX(radiation_level), MIN(radiation_level), COUNT(*)
                FROM measurements 
                WHERE DATE(timestamp) BETWEEN ? AND ?
                GROUP BY sensor_id
            ''', (start_date, end_date))

            results = cursor.fetchall()

            filename = f"radiation_weekly_report_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.csv"

            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Недельный отчет по уровню радиации'])
                writer.writerow([f"Период: {start_date} - {end_date}"])
                writer.writerow([])
                writer.writerow(['Датчик', 'Средний уровень', 'Максимум', 'Минимум', 'Измерений'])

                for row in results:
                    writer.writerow([
                        row[0],
                        f"{row[1]:.2f} мкЗв/ч",
                        f"{row[2]:.2f} мкЗв/ч",
                        f"{row[3]:.2f} мкЗв/ч",
                        row[4]
                    ])

            messagebox.showinfo("Успех", f"Недельный отчет создан:\n{filename}")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать отчет: {e}")

    def generate_monthly_report(self):
        """Генерация месячного отчета"""
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=30)

            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT sensor_id, AVG(radiation_level), MAX(radiation_level), MIN(radiation_level), COUNT(*)
                FROM measurements 
                WHERE DATE(timestamp) BETWEEN ? AND ?
                GROUP BY sensor_id
            ''', (start_date, end_date))

            results = cursor.fetchall()

            filename = f"radiation_monthly_report_{start_date.strftime('%Y%m')}.csv"

            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Месячный отчет по уровню радиации'])
                writer.writerow([f"Период: {start_date} - {end_date}"])
                writer.writerow([])
                writer.writerow(['Датчик', 'Средний уровень', 'Максимум', 'Минимум', 'Измерений'])

                for row in results:
                    writer.writerow([
                        row[0],
                        f"{row[1]:.2f} мкЗв/ч",
                        f"{row[2]:.2f} мкЗв/ч",
                        f"{row[3]:.2f} мкЗв/ч",
                        row[4]
                    ])

            messagebox.showinfo("Успех", f"Месячный отчет создан:\n{filename}")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать отчет: {e}")

    def generate_statistical_report(self):
        """Генерация статистического отчета"""
        try:
            cursor = self.conn.cursor()

            # Статистика за все время
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_measurements,
                    AVG(radiation_level) as avg_level,
                    MAX(radiation_level) as max_level,
                    MIN(radiation_level) as min_level,
                    COUNT(CASE WHEN status != 'НОРМА' THEN 1 END) as alerts_count
                FROM measurements
            ''')

            stats = cursor.fetchone()

            filename = f"radiation_statistical_report_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"

            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Статистический отчет системы контроля радиации'])
                writer.writerow([f"Сформирован: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"])
                writer.writerow([])
                writer.writerow(['Параметр', 'Значение'])
                writer.writerow(['Всего измерений', stats[0]])
                writer.writerow(['Средний уровень', f"{stats[1]:.3f} мкЗв/ч"])
                writer.writerow(['Максимальный уровень', f"{stats[2]:.2f} мкЗв/ч"])
                writer.writerow(['Минимальный уровень', f"{stats[3]:.2f} мкЗв/ч"])
                writer.writerow(['Количество предупреждений', stats[4]])
                writer.writerow(['Процент аномалий', f"{(stats[4] / stats[0] * 100 if stats[0] > 0 else 0):.1f}%"])

            messagebox.showinfo("Успех", f"Статистический отчет создан:\n{filename}")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать отчет: {e}")

    def generate_events_report(self):
        """Генерация отчета по событиям"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT timestamp, sensor_id, alert_type, actual_value, threshold_value
                FROM alerts
                ORDER BY timestamp DESC
            ''')

            events = cursor.fetchall()

            filename = f"radiation_events_report_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"

            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Отчет по событиям системы контроля радиации'])
                writer.writerow([f"Сформирован: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"])
                writer.writerow([])
                writer.writerow(['Время', 'Датчик', 'Тип события', 'Фактический уровень', 'Пороговый уровень'])

                for event in events:
                    writer.writerow([
                        event[0],
                        event[1],
                        event[2],
                        f"{event[3]:.2f} мкЗв/ч",
                        f"{event[4]} мкЗв/ч"
                    ])

            messagebox.showinfo("Успех", f"Отчет по событиям создан:\n{filename}")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать отчет: {e}")

    def export_all_data(self):
        """Экспорт всех данных"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT m.timestamp, s.sensor_id, s.location, m.radiation_level, m.status
                FROM measurements m
                JOIN sensors s ON m.sensor_id = s.sensor_id
                ORDER BY m.timestamp
            ''')

            data = cursor.fetchall()

            filename = f"radiation_export_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"

            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Время', 'Датчик', 'Участок', 'Уровень радиации', 'Статус'])

                for row in data:
                    writer.writerow([
                        row[0],
                        row[1],
                        row[2],
                        f"{row[3]:.2f} мкЗв/ч",
                        row[4]
                    ])

            messagebox.showinfo("Успех", f"Данные экспортированы:\n{filename}\nЗаписей: {len(data)}")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось экспортировать данные: {e}")

    def update_statistics(self):
        """Обновление статистики на панели"""
        try:
            cursor = self.conn.cursor()

            # Общее количество измерений
            cursor.execute('SELECT COUNT(*) FROM measurements')
            total_measurements = cursor.fetchone()[0]

            # Измерения за сегодня
            today = datetime.now().date()
            cursor.execute('SELECT COUNT(*) FROM measurements WHERE DATE(timestamp) = ?', (today,))
            today_measurements = cursor.fetchone()[0]

            # Количество превышений
            cursor.execute('SELECT COUNT(*) FROM measurements WHERE status != "НОРМА"')
            alerts_count = cursor.fetchone()[0]

            # Обновление меток
            self.stats_labels["Всего измерений:"].config(text=str(total_measurements))
            self.stats_labels["За сегодня:"].config(text=str(today_measurements))
            self.stats_labels["Превышений порога:"].config(text=str(alerts_count))
            self.stats_labels["Последнее обновление:"].config(text=datetime.now().strftime('%H:%M:%S'))

        except Exception as e:
            self.logger.error(f"Ошибка обновления статистики: {e}")

    def update_db_statistics(self):
        """Обновление статистики БД"""
        try:
            cursor = self.conn.cursor()

            # Общее количество записей
            cursor.execute('SELECT COUNT(*) FROM measurements')
            total_records = cursor.fetchone()[0]

            # Размер БД (приблизительно)
            db_size = 0
            if os.path.exists('radiation_monitoring.db'):
                db_size = os.path.getsize('radiation_monitoring.db') / (1024 * 1024)  # в МБ

            # Первая и последняя записи
            cursor.execute('SELECT MIN(timestamp), MAX(timestamp) FROM measurements')
            time_range = cursor.fetchone()

            first_record = time_range[0] if time_range[0] else "--"
            last_record = time_range[1] if time_range[1] else "--"

            # Обновление меток
            self.db_stats_labels["Всего записей:"].config(text=str(total_records))
            self.db_stats_labels["Размер БД:"].config(text=f"{db_size:.2f} МБ")
            self.db_stats_labels["Первая запись:"].config(text=str(first_record)[:19])
            self.db_stats_labels["Последняя запись:"].config(text=str(last_record)[:19])

        except Exception as e:
            self.logger.error(f"Ошибка обновления статистики БД: {e}")

    def load_recent_measurements(self):
        """Загрузка последних измерений в таблицу"""
        try:
            # Очистка таблицы
            for item in self.data_tree.get_children():
                self.data_tree.delete(item)

            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT m.timestamp, m.sensor_id, s.location, m.radiation_level, m.status
                FROM measurements m
                JOIN sensors s ON m.sensor_id = s.sensor_id
                ORDER BY m.timestamp DESC
                LIMIT 100
            ''')

            for row in cursor.fetchall():
                self.data_tree.insert("", "end", values=(
                    row[0],
                    row[1],
                    row[2],
                    f"{row[3]:.2f} мкЗв/ч",
                    row[4]
                ))

        except Exception as e:
            self.logger.error(f"Ошибка загрузки измерений: {e}")

    def update_alerts_tree(self):
        """Обновление дерева оповещений"""
        try:
            # Очистка таблицы
            for item in self.alerts_tree.get_children():
                self.alerts_tree.delete(item)

            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT timestamp, sensor_id, alert_type, actual_value, threshold_value,
                       CASE WHEN notified = 1 THEN 'Отправлено' ELSE 'В ожидании' END
                FROM alerts
                ORDER BY timestamp DESC
                LIMIT 50
            ''')

            for row in cursor.fetchall():
                self.alerts_tree.insert("", "end", values=(
                    row[0],
                    row[1],
                    row[2],
                    f"{row[3]:.2f} мкЗв/ч",
                    f"{row[4]} мкЗв/ч",
                    row[5]
                ))

        except Exception as e:
            self.logger.error(f"Ошибка обновления оповещений: {e}")

    def save_settings(self):
        """Сохранение настроек"""
        try:
            # Обновление конфигурации из полей ввода
            self.config['polling_interval'] = int(self.settings_entries['polling_interval'].get())
            self.config['warning_threshold'] = float(self.settings_entries['warning_threshold'].get())
            self.config['danger_threshold'] = float(self.settings_entries['danger_threshold'].get())
            self.config['smtp_server'] = self.settings_entries['smtp_server'].get()
            self.config['smtp_port'] = int(self.settings_entries['smtp_port'].get())
            self.config['notification_email'] = self.settings_entries['notification_email'].get()

            # Сохранение в файл
            with open('system_config.json', 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)

            messagebox.showinfo("Успех", "Настройки сохранены!")
            self.logger.info("Настройки системы обновлены")

        except ValueError as e:
            messagebox.showerror("Ошибка", "Проверьте корректность числовых значений!")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить настройки: {e}")

    def save_notification_settings(self):
        """Сохранение настроек оповещений"""
        try:
            self.config['warning_threshold'] = float(self.warning_threshold_var.get())
            self.config['danger_threshold'] = float(self.danger_threshold_var.get())

            # Обновление контактов
            contacts_text = self.contacts_text.get("1.0", "end-1c")
            self.emergency_contacts = [line.strip() for line in contacts_text.split('\n') if line.strip()]

            messagebox.showinfo("Успех", "Настройки оповещений сохранены!")

        except ValueError:
            messagebox.showerror("Ошибка", "Проверьте корректность пороговых значений!")

    def reset_settings(self):
        """Сброс настроек к умолчаниям"""
        default_config = {
            'polling_interval': 5,
            'warning_threshold': 1.0,
            'danger_threshold': 2.5,
            'smtp_server': 'smtp.company.com',
            'smtp_port': 587,
            'notification_email': 'safety@company.com'
        }

        for key, entry in self.settings_entries.items():
            entry.delete(0, tk.END)
            entry.insert(0, str(default_config.get(key, "")))

        messagebox.showinfo("Сброс", "Настройки сброшены к умолчаниям!")

    # Методы для диалоговых окон (заглушки)
    def show_add_sensor_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Добавление датчика")
        dialog.geometry("400x300")
        ttk.Label(dialog, text="Функция добавления датчика в разработке", font=("Arial", 12)).pack(pady=50)
        ttk.Button(dialog, text="Закрыть", command=dialog.destroy).pack(pady=10)

    def show_edit_sensor_dialog(self):
        messagebox.showinfo("Инфо", "Функция редактирования датчика в разработке")

    def show_calibration_dialog(self):
        messagebox.showinfo("Инфо", "Функция калибровки в разработке")

    def refresh_sensors_table(self):
        messagebox.showinfo("Инфо", "Таблица датчиков обновлена")

    def manual_data_collection(self):
        """Ручной сбор данных"""
        self.collect_sensor_data()
        messagebox.showinfo("Обновление", "Данные обновлены вручную")

    def reset_alarms(self):
        """Сброс аварийных сигналов"""
        self.logger.info("Аварийные сигналы сброшены оператором")
        messagebox.showinfo("Сброс", "Аварийные сигналы сброшены!")

    def clear_alerts_log(self):
        """Очистка журнала оповещений"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM alerts')
            self.conn.commit()
            self.update_alerts_tree()
            messagebox.showinfo("Очистка", "Журнал оповещений очищен")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось очистить журнал: {e}")

    def create_backup(self):
        """Создание резервной копии"""
        try:
            import shutil
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"radiation_system_backup_{timestamp}.db"
            shutil.copy2('radiation_monitoring.db', backup_file)
            messagebox.showinfo("Резервная копия", f"Резервная копия создана:\n{backup_file}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать резервную копию: {e}")

    def restore_backup(self):
        """Восстановление из резервной копии"""
        messagebox.showinfo("Инфо", "Функция восстановления в разработке")

    def run(self):
        """Запуск приложения"""
        try:
            self.logger.info("Запуск системы контроля уровня радиации")
            self.root.mainloop()
        except Exception as e:
            self.logger.critical(f"Критическая ошибка при запуске: {e}")
        finally:
            self.data_collection_active = False
            if hasattr(self, 'conn'):
                self.conn.close()
            self.logger.info("Система остановлена")


# Запуск приложения
if __name__ == "__main__":
    app = RadiationMonitoringSystem()
    app.run()
