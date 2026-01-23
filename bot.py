import telebot
from telebot import types
import os
from dotenv import load_dotenv
import json
from datetime import datetime, timedelta
import threading
import time
from pathlib import Path

# Импортируем функции из weather_app
from weather_app import (
    get_weather,
    get_weather_by_coordinates,
    get_weather_by_hour,
    get_weather_pollution
)

# Загружаем переменные окружения
load_dotenv()

# Инициализация бота
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не установлен в файле .env!")

bot = telebot.TeleBot(BOT_TOKEN)

# Путь к файлу для хранения данных пользователей
BASE_DIR = Path(__file__).resolve().parent
USER_DATA_FILE = BASE_DIR / "user_data.json"

# Глобальное хранилище данных пользователей
user_data = {}

# Смайлики для погоды
WEATHER_EMOJI = {
    "ясно": "☀️",
    "облачно": "☁️",
    "пасмурно": "☁️",
    "дождь": "🌧️",
    "небольшой дождь": "🌦️",
    "гроза": "⛈️",
    "снег": "❄️",
    "туман": "🌫️",
    "ветер": "💨"
}


def get_main_menu():
    """Создает главное меню с кнопками"""
    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=False,
        is_persistent=True
    )
    
    # Первый ряд
    btn1 = types.KeyboardButton("🏙️ Погода в городе")
    btn2 = types.KeyboardButton("📅 Прогноз на 5 дней")
    markup.row(btn1, btn2)
    
    # Второй ряд
    btn3 = types.KeyboardButton("📍 Моё местоположение")
    btn4 = types.KeyboardButton("🔔 Уведомления")
    markup.row(btn3, btn4)
    
    # Третий ряд
    btn5 = types.KeyboardButton("⚖️ Сравнить города")
    btn6 = types.KeyboardButton("📊 Расширенные данные")
    markup.row(btn5, btn6)
    
    # Четвертый ряд
    btn7 = types.KeyboardButton("❓ Помощь")
    markup.row(btn7)
    
    return markup


def get_back_menu():
    """Создает меню с кнопкой возврата"""
    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True,
        is_persistent=True
    )
    markup.row(types.KeyboardButton("◀️ Главное меню"))
    return markup


def load_user_data():
    """Загружает данные пользователей из файла"""
    global user_data
    if USER_DATA_FILE.exists():
        try:
            with open(USER_DATA_FILE, "r", encoding="utf-8") as f:
                user_data = json.load(f)
        except Exception as e:
            print(f"Ошибка при загрузке данных пользователей: {e}")
            user_data = {}
    else:
        user_data = {}


def save_user_data():
    """Сохраняет данные пользователей в файл"""
    try:
        with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(user_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Ошибка при сохранении данных пользователей: {e}")


def get_user_id_str(user_id):
    """Преобразует ID пользователя в строку для использования в словаре"""
    return str(user_id)


def get_weather_emoji(description):
    """Возвращает смайлик для описания погоды"""
    description_lower = description.lower()
    for key, emoji in WEATHER_EMOJI.items():
        if key in description_lower:
            return emoji
    return "🌍"


def format_weather_message(data, city_name=None):
    """Форматирует данные о погоде в красивое сообщение"""
    if not data:
        return "❌ Не удалось получить данные о погоде"
    
    # Основные данные
    temp = data.get("main", {}).get("temp", "N/A")
    feels_like = data.get("main", {}).get("feels_like", "N/A")
    humidity = data.get("main", {}).get("humidity", "N/A")
    pressure = data.get("main", {}).get("pressure", "N/A")
    wind_speed = data.get("wind", {}).get("speed", "N/A")
    description = data.get("weather", [{}])[0].get("description", "N/A")
    city = city_name or data.get("name", "Неизвестно")
    
    emoji = get_weather_emoji(description)
    
    message = f"{emoji} <b>Погода в городе {city}</b>\n\n"
    message += f"🌡️ Температура: <b>{temp}°C</b>\n"
    message += f"🤔 Ощущается как: <b>{feels_like}°C</b>\n"
    message += f"💧 Влажность: <b>{humidity}%</b>\n"
    message += f"🌪️ Ветер: <b>{wind_speed} м/с</b>\n"
    message += f"📊 Давление: <b>{pressure} мм рт. ст.</b>\n"
    message += f"📝 Описание: <b>{description.capitalize()}</b>"
    
    return message


def format_extended_weather_message(weather_data, pollution_data=None):
    """Форматирует расширенные данные о погоде"""
    if not weather_data:
        return "❌ Не удалось получить данные о погоде"
    
    # Основные данные
    temp = weather_data.get("main", {}).get("temp", "N/A")
    feels_like = weather_data.get("main", {}).get("feels_like", "N/A")
    humidity = weather_data.get("main", {}).get("humidity", "N/A")
    pressure = weather_data.get("main", {}).get("pressure", "N/A")
    wind_speed = weather_data.get("wind", {}).get("speed", "N/A")
    description = weather_data.get("weather", [{}])[0].get("description", "N/A")
    city = weather_data.get("name", "Неизвестно")
    clouds = weather_data.get("clouds", {}).get("all", "N/A")
    
    # Время восхода и заката
    sys_data = weather_data.get("sys", {})
    sunrise = sys_data.get("sunrise")
    sunset = sys_data.get("sunset")
    
    sunrise_str = datetime.fromtimestamp(sunrise).strftime("%H:%M") if sunrise else "N/A"
    sunset_str = datetime.fromtimestamp(sunset).strftime("%H:%M") if sunset else "N/A"
    
    emoji = get_weather_emoji(description)
    
    message = f"{emoji} <b>Расширенная информация о погоде</b>\n"
    message += f"📍 <b>Город:</b> {city}\n\n"
    
    message += f"<b>🌡️ ТЕМПЕРАТУРА</b>\n"
    message += f"  • Текущая: <b>{temp}°C</b>\n"
    message += f"  • Ощущается: <b>{feels_like}°C</b>\n\n"
    
    message += f"<b>💨 ВЕТЕР И АТМОСФЕРА</b>\n"
    message += f"  • Скорость ветра: <b>{wind_speed} м/с</b>\n"
    message += f"  • Давление: <b>{pressure} мм рт. ст.</b>\n"
    message += f"  • Влажность: <b>{humidity}%</b>\n"
    message += f"  • Облачность: <b>{clouds}%</b>\n\n"
    
    message += f"<b>🌅 СОЛНЦЕ</b>\n"
    message += f"  • Восход: <b>{sunrise_str}</b>\n"
    message += f"  • Закат: <b>{sunset_str}</b>\n\n"
    
    # Добавляем данные о загрязнении, если они есть
    if pollution_data and "list" in pollution_data and pollution_data["list"]:
        components = pollution_data["list"][0].get("components", {})
        aqi = pollution_data["list"][0].get("main", {}).get("aqi", "N/A")
        
        aqi_text = {
            1: "Отличное 🟢",
            2: "Хорошее 🟡",
            3: "Умеренное 🟠",
            4: "Плохое 🔴",
            5: "Очень плохое 🟣"
        }
        
        message += f"<b>🏭 КАЧЕСТВО ВОЗДУХА</b>\n"
        message += f"  • Общий индекс: <b>{aqi_text.get(aqi, 'N/A')}</b>\n"
        
        if components:
            message += f"  • PM2.5: <b>{components.get('pm2_5', 'N/A')} µg/m³</b>\n"
            message += f"  • PM10: <b>{components.get('pm10', 'N/A')} µg/m³</b>\n"
            message += f"  • CO: <b>{components.get('co', 'N/A')} µg/m³</b>\n"
    
    message += f"\n📝 <b>Описание:</b> {description.capitalize()}"
    
    return message


# ==================== КОМАНДЫ БОТА ====================

@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    """Приветственное сообщение и меню"""
    user_id = get_user_id_str(message.from_user.id)
    if user_id not in user_data:
        user_data[user_id] = {
            "notifications": False,
            "location": None,
            "last_check": None
        }
        save_user_data()
    
    welcome_text = """🌤️ <b>Добро пожаловать в WeatherBot!</b>

Я помогу вам узнать погоду в любой точке мира! 🌍

<b>📋 Выберите действие из меню ниже:</b>

Нажмите на кнопки внизу экрана 👇"""
    
    # Создаем клавиатуру
    keyboard = get_main_menu()
    print("✅ Отправка сообщения с клавиатурой...")  # Отладка
    
    bot.send_message(
        message.chat.id, 
        welcome_text, 
        parse_mode="HTML", 
        reply_markup=keyboard
    )


# ==================== ОБРАБОТЧИКИ КНОПОК МЕНЮ ====================

@bot.message_handler(func=lambda message: message.text == "◀️ Главное меню")
def back_to_main_menu(message):
    """Возврат в главное меню"""
    welcome_text = """🌤️ <b>Главное меню WeatherBot</b>

Выберите нужное действие из меню ниже 👇"""
    bot.send_message(message.chat.id, welcome_text, parse_mode="HTML", reply_markup=get_main_menu())


@bot.message_handler(func=lambda message: message.text == "🏙️ Погода в городе")
def menu_weather(message):
    """Обработчик кнопки 'Погода в городе'"""
    msg = bot.send_message(
        message.chat.id,
        "🏙️ Введите название города на русском или английском языке:",
        reply_markup=get_back_menu()
    )
    bot.register_next_step_handler(msg, process_weather_city)


@bot.message_handler(func=lambda message: message.text == "📅 Прогноз на 5 дней")
def menu_forecast(message):
    """Обработчик кнопки 'Прогноз на 5 дней'"""
    forecast_command(message)


@bot.message_handler(func=lambda message: message.text == "📍 Моё местоположение")
def menu_location(message):
    """Обработчик кнопки 'Моё местоположение'"""
    location_command(message)


@bot.message_handler(func=lambda message: message.text == "🔔 Уведомления")
def menu_notifications(message):
    """Обработчик кнопки 'Уведомления'"""
    notifications_command(message)


@bot.message_handler(func=lambda message: message.text == "⚖️ Сравнить города")
def menu_compare(message):
    """Обработчик кнопки 'Сравнить города'"""
    msg = bot.send_message(
        message.chat.id,
        "⚖️ Введите два города через запятую для сравнения.\n\nНапример: <code>Москва, Санкт-Петербург</code>",
        parse_mode="HTML",
        reply_markup=get_back_menu()
    )
    bot.register_next_step_handler(msg, process_compare_cities)


@bot.message_handler(func=lambda message: message.text == "📊 Расширенные данные")
def menu_extended(message):
    """Обработчик кнопки 'Расширенные данные'"""
    msg = bot.send_message(
        message.chat.id,
        "📊 <b>Расширенные данные о погоде</b>\n\nВведите название города или покажите местоположение:",
        parse_mode="HTML",
        reply_markup=get_back_menu()
    )
    bot.register_next_step_handler(msg, process_extended_data)


@bot.message_handler(func=lambda message: message.text == "❓ Помощь")
def menu_help(message):
    """Обработчик кнопки 'Помощь'"""
    send_welcome(message)


# ==================== КОМАНДЫ БОТА ====================

@bot.message_handler(commands=["menu"])
def show_menu_command(message):
    """Команда для принудительного показа меню"""
    keyboard = get_main_menu()
    bot.send_message(
        message.chat.id,
        "📱 Меню отображено! Кнопки должны появиться внизу экрана.",
        reply_markup=keyboard
    )


@bot.message_handler(commands=["weather"])
def weather_command(message):
    """Команда для получения погоды по городу"""
    msg = bot.send_message(
        message.chat.id,
        "🏙️ Введите название города на русском или английском языке:"
    )
    bot.register_next_step_handler(msg, process_weather_city)


def process_weather_city(message):
    """Обрабатывает название города и отправляет погоду"""
    # Проверка на возврат в меню
    if message.text == "◀️ Главное меню":
        back_to_main_menu(message)
        return
    
    city = message.text.strip()
    
    if not city:
        bot.send_message(message.chat.id, "❌ Вы не ввели название города!", reply_markup=get_main_menu())
        return
    
    # Показываем индикатор загрузки
    bot.send_chat_action(message.chat.id, "typing")
    
    # Получаем данные о погоде
    weather_data = get_weather(city)
    
    if weather_data:
        # Сохраняем местоположение пользователя
        user_id = get_user_id_str(message.from_user.id)
        coord = weather_data.get("coord", {})
        if coord:
            user_data[user_id]["location"] = {
                "lat": coord.get("lat"),
                "lon": coord.get("lon"),
                "city": weather_data.get("name", city)
            }
            save_user_data()
        
        weather_msg = format_weather_message(weather_data)
        bot.send_message(message.chat.id, weather_msg, parse_mode="HTML", reply_markup=get_main_menu())
    else:
        bot.send_message(
            message.chat.id,
            f"❌ Не удалось найти город '{city}'. Проверьте правильность написания.",
            reply_markup=get_main_menu()
        )


@bot.message_handler(commands=["forecast"])
def forecast_command(message):
    """Команда для получения прогноза на 5 дней"""
    user_id = get_user_id_str(message.from_user.id)
    
    if user_id not in user_data or not user_data[user_id].get("location"):
        bot.send_message(
            message.chat.id,
            "❌ Сначала покажите своё местоположение через /location или узнайте погоду в городе через /weather"
        )
        return
    
    location = user_data[user_id]["location"]
    lat = location["lat"]
    lon = location["lon"]
    
    bot.send_chat_action(message.chat.id, "typing")
    
    # Получаем прогноз
    forecast_data = get_weather_by_hour(lat, lon)
    
    if forecast_data and "list" in forecast_data:
        show_forecast_menu(message.chat.id, forecast_data, location.get("city", "Ваше местоположение"))
    else:
        bot.send_message(message.chat.id, "❌ Не удалось получить прогноз погоды")


def show_forecast_menu(chat_id, forecast_data, city_name):
    """Показывает меню выбора дня прогноза"""
    # Группируем прогноз по дням
    days_data = {}
    
    for item in forecast_data.get("list", []):
        dt = datetime.fromtimestamp(item["dt"])
        date_key = dt.strftime("%Y-%m-%d")
        day_name = dt.strftime("%d.%m (%a)")
        
        if date_key not in days_data:
            days_data[date_key] = {
                "date": dt,
                "day_name": day_name,
                "forecasts": []
            }
        days_data[date_key]["forecasts"].append(item)
    
    # Создаем inline-клавиатуру
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    for date_key, day_info in list(days_data.items())[:5]:  # Берем только 5 дней
        # Получаем среднюю температуру за день
        temps = [f["main"]["temp"] for f in day_info["forecasts"]]
        avg_temp = sum(temps) / len(temps)
        
        # Получаем наиболее частое описание погоды
        descriptions = [f["weather"][0]["description"] for f in day_info["forecasts"]]
        most_common_desc = max(set(descriptions), key=descriptions.count)
        emoji = get_weather_emoji(most_common_desc)
        
        button_text = f"{emoji} {day_info['day_name']} ({avg_temp:.1f}°C)"
        callback_data = f"forecast_{date_key}"
        
        markup.add(types.InlineKeyboardButton(text=button_text, callback_data=callback_data))
    
    markup.add(types.InlineKeyboardButton(text="❌ Закрыть", callback_data="close_forecast"))
    
    message_text = f"📅 <b>Прогноз погоды на 5 дней</b>\n📍 {city_name}\n\nВыберите день для подробной информации:"
    
    bot.send_message(chat_id, message_text, reply_markup=markup, parse_mode="HTML")


@bot.callback_query_handler(func=lambda call: call.data.startswith("forecast_"))
def forecast_day_callback(call):
    """Обработчик нажатия на день в прогнозе"""
    date_key = call.data.replace("forecast_", "")
    user_id = get_user_id_str(call.from_user.id)
    
    location = user_data[user_id]["location"]
    lat = location["lat"]
    lon = location["lon"]
    
    # Получаем прогноз заново
    forecast_data = get_weather_by_hour(lat, lon)
    
    if not forecast_data or "list" not in forecast_data:
        bot.answer_callback_query(call.id, "❌ Ошибка получения данных")
        return
    
    # Находим прогнозы для выбранного дня
    day_forecasts = []
    for item in forecast_data["list"]:
        dt = datetime.fromtimestamp(item["dt"])
        if dt.strftime("%Y-%m-%d") == date_key:
            day_forecasts.append(item)
    
    if not day_forecasts:
        bot.answer_callback_query(call.id, "❌ Данные не найдены")
        return
    
    # Форматируем детальное сообщение
    first_dt = datetime.fromtimestamp(day_forecasts[0]["dt"])
    day_str = first_dt.strftime("%d.%m.%Y (%A)")
    
    message = f"📅 <b>Детальный прогноз на {day_str}</b>\n"
    message += f"📍 {location.get('city', 'Ваше местоположение')}\n\n"
    
    for forecast in day_forecasts:
        dt = datetime.fromtimestamp(forecast["dt"])
        time_str = dt.strftime("%H:%M")
        temp = forecast["main"]["temp"]
        feels_like = forecast["main"]["feels_like"]
        description = forecast["weather"][0]["description"]
        wind = forecast["wind"]["speed"]
        humidity = forecast["main"]["humidity"]
        emoji = get_weather_emoji(description)
        
        message += f"🕐 <b>{time_str}</b>\n"
        message += f"{emoji} {temp:.1f}°C (ощущ. {feels_like:.1f}°C)\n"
        message += f"💨 {wind} м/с | 💧 {humidity}%\n"
        message += f"📝 {description.capitalize()}\n\n"
    
    # Создаем кнопку "Назад"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text="◀️ Назад к выбору дня", callback_data="back_to_forecast"))
    markup.add(types.InlineKeyboardButton(text="❌ Закрыть", callback_data="close_forecast"))
    
    # Удаляем предыдущее сообщение и отправляем новое
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    
    bot.send_message(call.message.chat.id, message, reply_markup=markup, parse_mode="HTML")
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "back_to_forecast")
def back_to_forecast_callback(call):
    """Возврат к меню выбора дня"""
    user_id = get_user_id_str(call.from_user.id)
    location = user_data[user_id]["location"]
    lat = location["lat"]
    lon = location["lon"]
    
    forecast_data = get_weather_by_hour(lat, lon)
    
    # Удаляем текущее сообщение
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    
    show_forecast_menu(call.message.chat.id, forecast_data, location.get("city", "Ваше местоположение"))
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "close_forecast")
def close_forecast_callback(call):
    """Закрытие меню прогноза"""
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    bot.answer_callback_query(call.id, "✅ Закрыто")


@bot.message_handler(commands=["location"])
def location_command(message):
    """Команда для запроса местоположения"""
    markup = types.ReplyKeyboardMarkup(
        one_time_keyboard=True,
        resize_keyboard=True
    )
    button = types.KeyboardButton(text="📍 Показать местоположение", request_location=True)
    markup.add(button)
    markup.add(types.KeyboardButton(text="❌ Отмена"))
    
    bot.send_message(
        message.chat.id,
        "📍 Нажмите на кнопку ниже, чтобы показать своё местоположение:",
        reply_markup=markup
    )


@bot.message_handler(func=lambda message: message.text and message.text == "❌ Отмена")
def cancel_location(message):
    """Обработчик отмены отправки местоположения"""
    bot.send_message(
        message.chat.id,
        "❌ Отменено.",
        reply_markup=get_main_menu()
    )


@bot.message_handler(content_types=["location"])
def handle_location(message):
    """Обработчик получения местоположения"""
    try:
        lat = message.location.latitude
        lon = message.location.longitude
        
        bot.send_chat_action(message.chat.id, "typing")
        
        # Получаем погоду по координатам
        weather_data = get_weather_by_coordinates(lat, lon)
        
        if weather_data:
            # Сохраняем местоположение пользователя
            user_id = get_user_id_str(message.from_user.id)
            
            # Инициализируем user_data для пользователя, если его нет
            if user_id not in user_data:
                user_data[user_id] = {
                    "notifications": False,
                    "location": None,
                    "last_check": None
                }
            
            user_data[user_id]["location"] = {
                "lat": lat,
                "lon": lon,
                "city": weather_data.get("name", "Ваше местоположение")
            }
            save_user_data()
            
            weather_msg = format_weather_message(weather_data)
            
            bot.send_message(message.chat.id, weather_msg, parse_mode="HTML")
            bot.send_message(
                message.chat.id,
                "✅ Ваше местоположение сохранено! Теперь вы можете использовать прогноз на 5 дней.",
                reply_markup=get_main_menu()
            )
        else:
            bot.send_message(
                message.chat.id,
                "❌ Не удалось получить погоду для данного местоположения.\n\n🔑 Проверьте, что API_KEY установлен в файле .env",
                reply_markup=get_main_menu()
            )
    except Exception as e:
        print(f"Ошибка при обработке местоположения: {e}")
        bot.send_message(
            message.chat.id,
            "❌ Произошла ошибка при обработке вашего местоположения. Попробуйте позже.",
            reply_markup=get_main_menu()
        )


@bot.message_handler(commands=["notifications"])
def notifications_command(message):
    """Управление уведомлениями"""
    user_id = get_user_id_str(message.from_user.id)
    
    if user_id not in user_data:
        user_data[user_id] = {
            "notifications": False,
            "location": None,
            "last_check": None
        }
    
    current_status = user_data[user_id].get("notifications", False)
    location = user_data[user_id].get("location")
    
    markup = types.InlineKeyboardMarkup()
    
    if not location:
        bot.send_message(
            message.chat.id,
            "❌ Сначала покажите местоположение через /location или /weather"
        )
        return
    
    if current_status:
        status_text = "🔔 <b>Уведомления включены</b>\n\nВы будете получать уведомления о погоде каждые 2 часа."
        markup.add(types.InlineKeyboardButton(text="🔕 Отключить уведомления", callback_data="notif_off"))
    else:
        status_text = "🔕 <b>Уведомления отключены</b>\n\nВключите уведомления, чтобы получать информацию о погоде каждые 2 часа."
        markup.add(types.InlineKeyboardButton(text="🔔 Включить уведомления", callback_data="notif_on"))
    
    bot.send_message(message.chat.id, status_text, reply_markup=markup, parse_mode="HTML")


@bot.callback_query_handler(func=lambda call: call.data.startswith("notif_"))
def notification_toggle_callback(call):
    """Переключатель уведомлений"""
    user_id = get_user_id_str(call.from_user.id)
    action = call.data.replace("notif_", "")
    
    if action == "on":
        user_data[user_id]["notifications"] = True
        user_data[user_id]["last_check"] = datetime.now().isoformat()
        save_user_data()
        bot.answer_callback_query(call.id, "✅ Уведомления включены!")
        bot.edit_message_text(
            "🔔 <b>Уведомления включены</b>\n\nВы будете получать уведомления о погоде каждые 2 часа.",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton(text="🔕 Отключить уведомления", callback_data="notif_off")
            )
        )
    else:
        user_data[user_id]["notifications"] = False
        save_user_data()
        bot.answer_callback_query(call.id, "✅ Уведомления отключены!")
        bot.edit_message_text(
            "🔕 <b>Уведомления отключены</b>\n\nВключите уведомления, чтобы получать информацию о погоде каждые 2 часа.",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton(text="🔔 Включить уведомления", callback_data="notif_on")
            )
        )


@bot.message_handler(commands=["compare"])
def compare_command(message):
    """Команда для сравнения погоды в двух городах"""
    msg = bot.send_message(
        message.chat.id,
        "⚖️ Введите два города через запятую для сравнения.\n\nНапример: <code>Москва, Санкт-Петербург</code>",
        parse_mode="HTML"
    )
    bot.register_next_step_handler(msg, process_compare_cities)


def process_compare_cities(message):
    """Обрабатывает сравнение двух городов"""
    # Проверка на возврат в меню
    if message.text == "◀️ Главное меню":
        back_to_main_menu(message)
        return
    
    cities_text = message.text.strip()
    
    if "," not in cities_text:
        bot.send_message(
            message.chat.id,
            "❌ Пожалуйста, введите два города через запятую.\nНапример: <code>Москва, Санкт-Петербург</code>",
            parse_mode="HTML",
            reply_markup=get_main_menu()
        )
        return
    
    cities = [city.strip() for city in cities_text.split(",")]
    
    if len(cities) != 2:
        bot.send_message(
            message.chat.id,
            "❌ Нужно ввести ровно два города через запятую.",
            reply_markup=get_main_menu()
        )
        return
    
    city1, city2 = cities
    
    bot.send_chat_action(message.chat.id, "typing")
    
    # Получаем погоду для обоих городов
    weather1 = get_weather(city1)
    weather2 = get_weather(city2)
    
    if not weather1:
        bot.send_message(message.chat.id, f"❌ Не удалось найти город '{city1}'", reply_markup=get_main_menu())
        return
    
    if not weather2:
        bot.send_message(message.chat.id, f"❌ Не удалось найти город '{city2}'", reply_markup=get_main_menu())
        return
    
    # Форматируем сравнение
    name1 = weather1.get("name", city1)
    name2 = weather2.get("name", city2)
    
    temp1 = weather1.get("main", {}).get("temp", 0)
    temp2 = weather2.get("main", {}).get("temp", 0)
    
    humidity1 = weather1.get("main", {}).get("humidity", 0)
    humidity2 = weather2.get("main", {}).get("humidity", 0)
    
    wind1 = weather1.get("wind", {}).get("speed", 0)
    wind2 = weather2.get("wind", {}).get("speed", 0)
    
    pressure1 = weather1.get("main", {}).get("pressure", 0)
    pressure2 = weather2.get("main", {}).get("pressure", 0)
    
    desc1 = weather1.get("weather", [{}])[0].get("description", "N/A")
    desc2 = weather2.get("weather", [{}])[0].get("description", "N/A")
    
    emoji1 = get_weather_emoji(desc1)
    emoji2 = get_weather_emoji(desc2)
    
    # Определяем, где теплее
    if temp1 > temp2:
        temp_compare = f"В {name1} теплее на {abs(temp1 - temp2):.1f}°C"
    elif temp2 > temp1:
        temp_compare = f"В {name2} теплее на {abs(temp1 - temp2):.1f}°C"
    else:
        temp_compare = "Температура одинаковая"
    
    message_text = f"⚖️ <b>Сравнение погоды</b>\n\n"
    message_text += f"<b>{'─' * 30}</b>\n"
    message_text += f"<b>{emoji1} {name1}</b> vs <b>{emoji2} {name2}</b>\n"
    message_text += f"<b>{'─' * 30}</b>\n\n"
    
    message_text += f"🌡️ <b>Температура:</b>\n"
    message_text += f"  • {name1}: <b>{temp1}°C</b>\n"
    message_text += f"  • {name2}: <b>{temp2}°C</b>\n"
    message_text += f"  ℹ️ {temp_compare}\n\n"
    
    message_text += f"💧 <b>Влажность:</b>\n"
    message_text += f"  • {name1}: <b>{humidity1}%</b>\n"
    message_text += f"  • {name2}: <b>{humidity2}%</b>\n\n"
    
    message_text += f"💨 <b>Ветер:</b>\n"
    message_text += f"  • {name1}: <b>{wind1} м/с</b>\n"
    message_text += f"  • {name2}: <b>{wind2} м/с</b>\n\n"
    
    message_text += f"📊 <b>Давление:</b>\n"
    message_text += f"  • {name1}: <b>{pressure1} мм</b>\n"
    message_text += f"  • {name2}: <b>{pressure2} мм</b>\n\n"
    
    message_text += f"📝 <b>Описание:</b>\n"
    message_text += f"  • {name1}: {desc1.capitalize()}\n"
    message_text += f"  • {name2}: {desc2.capitalize()}"
    
    bot.send_message(message.chat.id, message_text, parse_mode="HTML", reply_markup=get_main_menu())


@bot.message_handler(commands=["extended"])
def extended_command(message):
    """Команда для получения расширенных данных"""
    msg = bot.send_message(
        message.chat.id,
        "📊 <b>Расширенные данные о погоде</b>\n\nВведите название города или покажите местоположение:",
        parse_mode="HTML"
    )
    bot.register_next_step_handler(msg, process_extended_data)


def process_extended_data(message):
    """Обрабатывает запрос расширенных данных"""
    if message.content_type == "location":
        lat = message.location.latitude
        lon = message.location.longitude
        
        bot.send_chat_action(message.chat.id, "typing")
        
        weather_data = get_weather_by_coordinates(lat, lon)
        pollution_data = get_weather_pollution(lat, lon)
        
        if weather_data:
            extended_msg = format_extended_weather_message(weather_data, pollution_data)
            bot.send_message(message.chat.id, extended_msg, parse_mode="HTML", reply_markup=get_main_menu())
        else:
            bot.send_message(message.chat.id, "❌ Не удалось получить данные о погоде", reply_markup=get_main_menu())
    
    elif message.content_type == "text":
        # Проверка на возврат в меню
        if message.text == "◀️ Главное меню":
            back_to_main_menu(message)
            return
        
        city = message.text.strip()
        
        if not city:
            bot.send_message(message.chat.id, "❌ Вы не ввели название города!", reply_markup=get_main_menu())
            return
        
        bot.send_chat_action(message.chat.id, "typing")
        
        weather_data = get_weather(city)
        
        if weather_data:
            coord = weather_data.get("coord", {})
            lat = coord.get("lat")
            lon = coord.get("lon")
            
            pollution_data = None
            if lat and lon:
                pollution_data = get_weather_pollution(lat, lon)
            
            extended_msg = format_extended_weather_message(weather_data, pollution_data)
            bot.send_message(message.chat.id, extended_msg, parse_mode="HTML", reply_markup=get_main_menu())
        else:
            bot.send_message(
                message.chat.id,
                f"❌ Не удалось найти город '{city}'. Проверьте правильность написания.",
                reply_markup=get_main_menu()
            )


# ==================== СИСТЕМА УВЕДОМЛЕНИЙ ====================

def check_weather_notifications():
    """Проверяет и отправляет погодные уведомления"""
    while True:
        try:
            time.sleep(7200)  # 2 часа = 7200 секунд
            
            current_time = datetime.now()
            
            for user_id_str, user_info in user_data.items():
                if not user_info.get("notifications", False):
                    continue
                
                location = user_info.get("location")
                if not location:
                    continue
                
                last_check = user_info.get("last_check")
                if last_check:
                    last_check_dt = datetime.fromisoformat(last_check)
                    if (current_time - last_check_dt).total_seconds() < 7200:
                        continue
                
                # Получаем погоду
                lat = location["lat"]
                lon = location["lon"]
                city = location.get("city", "Ваше местоположение")
                
                weather_data = get_weather_by_coordinates(lat, lon)
                
                if weather_data:
                    # Проверяем, есть ли дождь или снег
                    weather_id = weather_data.get("weather", [{}])[0].get("id", 0)
                    description = weather_data.get("weather", [{}])[0].get("description", "")
                    
                    # Коды погоды: 2xx - гроза, 3xx - морось, 5xx - дождь, 6xx - снег
                    should_notify = False
                    alert_message = ""
                    
                    if 200 <= weather_id < 300:
                        should_notify = True
                        alert_message = "⛈️ Внимание! Ожидается гроза!"
                    elif 300 <= weather_id < 600:
                        should_notify = True
                        alert_message = "🌧️ Внимание! Ожидается дождь!"
                    elif 600 <= weather_id < 700:
                        should_notify = True
                        alert_message = "❄️ Внимание! Ожидается снег!"
                    
                    if should_notify:
                        notification_text = f"{alert_message}\n\n"
                        notification_text += format_weather_message(weather_data, city)
                        
                        try:
                            user_id_int = int(user_id_str)
                            bot.send_message(user_id_int, notification_text, parse_mode="HTML")
                        except Exception as e:
                            print(f"Ошибка отправки уведомления пользователю {user_id_str}: {e}")
                
                # Обновляем время последней проверки
                user_data[user_id_str]["last_check"] = current_time.isoformat()
            
            save_user_data()
            
        except Exception as e:
            print(f"Ошибка в системе уведомлений: {e}")
            time.sleep(60)  # Ждем минуту перед повтором при ошибке


# ==================== ЗАПУСК БОТА ====================

def main():
    """Главная функция запуска бота"""
    print("🤖 Загрузка данных пользователей...")
    load_user_data()
    
    print("🔔 Запуск системы уведомлений...")
    notification_thread = threading.Thread(target=check_weather_notifications, daemon=True)
    notification_thread.start()
    
    print("✅ WeatherBot запущен!")
    print("Нажмите Ctrl+C для остановки")
    
    bot.infinity_polling(timeout=60, long_polling_timeout=60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")
        save_user_data()
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        save_user_data()
