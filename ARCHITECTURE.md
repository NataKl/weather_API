# Архитектура WeatherBot 🏗️

## Общая схема

```
┌─────────────────────────────────────────────────────────────┐
│                        TELEGRAM BOT                          │
│                         (bot.py)                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ├─── /start, /help
                              │    └─► Приветственное меню
                              │
                              ├─── /weather (Функция 1)
                              │    └─► Прогноз по городу
                              │        └─► weather_app.get_weather()
                              │
                              ├─── /forecast (Функция 2)
                              │    └─► Прогноз на 5 дней
                              │        ├─► Inline клавиатура
                              │        ├─► Выбор дня
                              │        └─► weather_app.get_weather_by_hour()
                              │
                              ├─── /location (Функция 3)
                              │    └─► Геолокация
                              │        ├─► Кнопка местоположения
                              │        └─► weather_app.get_weather_by_coordinates()
                              │
                              ├─── /notifications (Функция 4)
                              │    └─► Погодные уведомления
                              │        ├─► Включение/выключение
                              │        └─► Фоновый поток (каждые 2 часа)
                              │
                              ├─── /compare (Функция 5)
                              │    └─► Сравнение городов
                              │        └─► 2x weather_app.get_weather()
                              │
                              └─── /extended (Функция 6)
                                   └─► Расширенные данные
                                       ├─► weather_app.get_weather()
                                       └─► weather_app.get_weather_pollution()

┌─────────────────────────────────────────────────────────────┐
│                    WEATHER API MODULE                        │
│                     (weather_app.py)                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ├─► get_weather(city)
                              │   └─► OpenWeatherMap Current Weather
                              │
                              ├─► get_weather_by_coordinates(lat, lon)
                              │   └─► OpenWeatherMap Current Weather
                              │
                              ├─► get_weather_by_hour(lat, lon)
                              │   └─► OpenWeatherMap 5 Day Forecast
                              │
                              └─► get_weather_pollution(lat, lon)
                                  └─► OpenWeatherMap Air Pollution

┌─────────────────────────────────────────────────────────────┐
│                      DATA STORAGE                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ├─► user_data.json
                              │   └─► {user_id: {location, notifications, ...}}
                              │
                              └─► weather_cache.json
                                  └─► Кэш погодных данных (3 часа)

┌─────────────────────────────────────────────────────────────┐
│                   BACKGROUND SERVICES                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              └─► Notification Thread
                                  ├─► Проверка каждые 2 часа
                                  ├─► Анализ погоды
                                  └─► Отправка уведомлений
```

## Поток данных

### Прогноз погоды (Функция 1)
```
Пользователь → /weather → Ввод города → get_weather() → OpenWeatherMap API
                                                       ↓
                                       Сохранение в user_data.json
                                                       ↓
                                       Форматирование сообщения
                                                       ↓
                                       Отправка пользователю
```

### Прогноз на 5 дней (Функция 2)
```
Пользователь → /forecast → Проверка местоположения
                                    ↓
                        get_weather_by_hour() → OpenWeatherMap API
                                    ↓
                        Группировка по дням (5 дней)
                                    ↓
                        Создание inline-клавиатуры
                                    ↓
                        Отправка меню выбора
                                    ↓
           [Пользователь выбирает день]
                                    ↓
                        Детальный почасовой прогноз
                                    ↓
                        Кнопки: [Назад] [Закрыть]
```

### Система уведомлений (Функция 4)
```
Фоновый поток → Ожидание 2 часа → Проверка user_data.json
                                           ↓
                              [Для каждого пользователя с notifications=true]
                                           ↓
                              get_weather_by_coordinates()
                                           ↓
                              Анализ погоды (дождь/снег/гроза?)
                                           ↓
                              [Да] → Отправка уведомления
                              [Нет] → Пропуск
                                           ↓
                              Обновление last_check
```

## Технологический стек

- **Python 3.x** - Основной язык
- **pyTelegramBotAPI** - Telegram Bot API wrapper
- **requests** - HTTP запросы к OpenWeatherMap
- **threading** - Фоновые уведомления
- **json** - Хранилище данных
- **datetime** - Обработка времени
- **pathlib** - Работа с путями

## Компоненты системы

### 1. Обработчики команд (bot.py)
- `send_welcome()` - /start, /help
- `weather_command()` - /weather
- `forecast_command()` - /forecast
- `location_command()` - /location
- `notifications_command()` - /notifications
- `compare_command()` - /compare
- `extended_command()` - /extended

### 2. Callback-обработчики
- `forecast_day_callback()` - Выбор дня в прогнозе
- `back_to_forecast_callback()` - Возврат к меню
- `close_forecast_callback()` - Закрытие меню
- `notification_toggle_callback()` - Вкл/выкл уведомлений

### 3. Утилиты
- `format_weather_message()` - Форматирование погоды
- `format_extended_weather_message()` - Расширенные данные
- `get_weather_emoji()` - Эмодзи по описанию
- `load_user_data()` - Загрузка данных
- `save_user_data()` - Сохранение данных

### 4. Фоновые сервисы
- `check_weather_notifications()` - Мониторинг погоды

## Масштабируемость

Текущая версия использует JSON для хранения, но легко заменяется на:
- **SQLite** для локальной БД
- **PostgreSQL/MySQL** для продакшена
- **Redis** для кэширования

## Безопасность

- Ключи API в .env файле
- .gitignore для защиты конфиденциальных данных
- Обработка ошибок API
- Таймауты для запросов

## Производительность

- Кэширование погодных данных (3 часа)
- Фоновый поток для уведомлений
- Удаление старых inline-сообщений
- Оптимизированные API запросы

---

**Архитектура спроектирована для**:
- Простоты понимания
- Легкости расширения
- Удобства поддержки
- Надежности работы
