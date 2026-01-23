import requests
from dotenv import load_dotenv 
import os
from urllib.parse import quote
from pathlib import Path
import json
from datetime import datetime, timedelta
from collections import defaultdict

# Получаем путь к директории, где находится скрипт
BASE_DIR = Path(__file__).resolve().parent
CACHE_FILE = BASE_DIR / 'weather_cache.json'

# Пробуем загрузить .env из текущей директории и из родительской
env_path = BASE_DIR / '.env'
env_loaded = load_dotenv(dotenv_path=env_path)
if not env_loaded:
    # Пробуем загрузить из родительской директории
    env_path = BASE_DIR.parent / '.env'
    env_loaded = load_dotenv(dotenv_path=env_path)


def save_weather_cache(data: dict, city: str = None, lat: float = None, lon: float = None) -> None:
    """
    Сохраняет данные о погоде в кэш с метаданными.
    """
    cache_data = {
        "city": city,
        "lat": lat,
        "lon": lon,
        "fetched_at": datetime.now().isoformat(),
        "weather_data": data
    }
    
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Ошибка при сохранении кэша: {e}")


def load_weather_cache() -> dict:
    """
    Загружает данные из кэша, если они существуют и не старше 3 часов.
    Возвращает словарь с данными или None, если кэш недействителен.
    """
    if not CACHE_FILE.exists():
        return None
    
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        # Проверяем возраст кэша
        fetched_at_str = cache_data.get("fetched_at")
        if not fetched_at_str:
            return None
        
        fetched_at = datetime.fromisoformat(fetched_at_str)
        age = datetime.now() - fetched_at
        
        # Кэш действителен, если ему меньше 3 часов
        if age < timedelta(hours=3):
            return cache_data
        else:
            return None
    except Exception as e:
        print(f"Ошибка при чтении кэша: {e}")
        return None


def format_cached_weather(cache_data: dict) -> None:
    """
    Форматирует и выводит данные о погоде из кэша.
    """
    weather_data = cache_data.get("weather_data", {})
    city = cache_data.get("city")
    lat = cache_data.get("lat")
    lon = cache_data.get("lon")
    fetched_at = cache_data.get("fetched_at")
    
    if weather_data:
        # Извлекаем данные из ответа
        temperature = weather_data.get("main", {}).get("temp")
        weather_description = weather_data.get("weather", [{}])[0].get("description", "нет данных")
        city_name = weather_data.get("name", city) if city else weather_data.get("name", "Неизвестно")
        
        # Получаем координаты из данных погоды
        coord = weather_data.get("coord", {})
        weather_lat = coord.get("lat")
        weather_lon = coord.get("lon")
        
        # Форматируем вывод
        if city:
            if weather_lat is not None and weather_lon is not None:
                print(f"Погода в {city_name} ({weather_lat}, {weather_lon}): {temperature}°C, {weather_description}")
            else:
                print(f"Погода в {city_name}: {temperature}°C, {weather_description}")
        elif lat is not None and lon is not None:
            print(f"Погода в {city_name} ({lat}, {lon}): {temperature}°C, {weather_description}")
        
        if fetched_at:
            fetched_dt = datetime.fromisoformat(fetched_at)
            age = datetime.now() - fetched_dt
            hours = int(age.total_seconds() // 3600)
            minutes = int((age.total_seconds() % 3600) // 60)
            print(f"(Данные из кэша, получены {hours}ч {minutes}мин назад)")

# 
def get_weather(city: str) -> dict:
    """
    Получает текущую погоду для указанного города.
    """
    api_key = os.getenv("API_KEY")
    
    if not api_key:
        print("Ошибка: API_KEY не установлен в переменных окружения!")
        env_path = BASE_DIR / '.env'
        print(f"Проверьте, что файл .env существует в директории: {BASE_DIR}")
        print(f"Файл должен содержать строку: API_KEY=ваш_ключ")
        if not env_path.exists():
            print(f"⚠️  Файл {env_path} не найден!")
        return None
    
    if city:
        # URL-кодируем название города для корректной обработки пробелов и спецсимволов
        encoded_city = quote(city)
        url = f"https://api.openweathermap.org/data/2.5/weather?q={encoded_city}&appid={api_key}&units=metric&lang=ru"
        
        try:
            # Добавляем таймаут 10 секунд для запроса
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                data = response.json()
                # Сохраняем в кэш
                save_weather_cache(data, city=city)
                
                # Извлекаем данные из ответа
                temperature = data.get("main", {}).get("temp")
                weather_description = data.get("weather", [{}])[0].get("description", "нет данных")
                city_name = data.get("name", city)  # Используем название из API или переданное значение
                
                # Получаем координаты из ответа
                coord = data.get("coord", {})
                lat = coord.get("lat")
                lon = coord.get("lon")
                
                # Форматируем вывод
                if lat is not None and lon is not None:
                    print(f"Погода в {city_name} ({lat}, {lon}): {temperature}°C, {weather_description}")
                else:
                    print(f"Погода в {city_name}: {temperature}°C, {weather_description}")
                return data
            elif response.status_code == 401:
                print("Ошибка: Неверный API ключ. Проверьте файл .env")
                return None
            elif response.status_code == 404:
                print(f"Ошибка: Город '{city}' не найден")
                return None
            else:
                print(f"Ошибка: {response.status_code} - {response.text}")
                return None
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError, requests.exceptions.RequestException) as e:
            print(f"Ошибка: Не удалось получить данные о погоде. {type(e).__name__}")
            
            # Предлагаем использовать кэш
            cache_data = load_weather_cache()
            if cache_data:
                print("\nХотите посмотреть данные из кэша? (да/нет): ", end="")
                user_choice = input().strip().lower()
                if user_choice in ['да', 'yes', 'y', 'д']:
                    format_cached_weather(cache_data)
                    return cache_data.get("weather_data")
            else:
                print("Кэш недоступен или устарел (старше 3 часов).")
            return None


def get_weather_by_coordinates(latitude: float, longitude: float) -> dict:
    """
    Получает текущую погоду по координатам.
    """
    api_key = os.getenv("API_KEY")
    
    if not api_key:
        print("Ошибка: API_KEY не установлен в переменных окружения!")
        env_path = BASE_DIR / '.env'
        print(f"Проверьте, что файл .env существует в директории: {BASE_DIR}")
        print(f"Файл должен содержать строку: API_KEY=ваш_ключ")
        return None
    
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={api_key}&units=metric&lang=ru"
    
    try:
        # Добавляем таймаут 10 секунд для запроса
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # Сохраняем в кэш
            save_weather_cache(data, lat=latitude, lon=longitude)
            
            # Получаем название города на русском через Nominatim (OpenStreetMap)
            city_name = "Неизвестно"
            try:
                # Используем Nominatim для получения локализованного названия на русском
                nominatim_url = f"https://nominatim.openstreetmap.org/reverse?lat={latitude}&lon={longitude}&format=json&accept-language=ru&addressdetails=1"
                headers = {'User-Agent': 'WeatherApp/1.0'}  # Требуется для Nominatim
                nominatim_response = requests.get(nominatim_url, headers=headers, timeout=10)
                if nominatim_response.status_code == 200:
                    nominatim_data = nominatim_response.json()
                    address = nominatim_data.get("address", {})
                    # Пробуем получить название города из разных полей
                    city_name = (address.get("city") or 
                                address.get("town") or 
                                address.get("village") or 
                                address.get("municipality") or
                                address.get("county") or
                                nominatim_data.get("display_name", "").split(",")[0] if nominatim_data.get("display_name") else None)
                    
                    # Если не получили название из Nominatim, пробуем OpenWeatherMap Geocoding
                    if not city_name:
                        geocode_url = f"http://api.openweathermap.org/geo/1.0/reverse?lat={latitude}&lon={longitude}&limit=1&appid={api_key}&lang=ru"
                        geocode_response = requests.get(geocode_url, timeout=10)
                        if geocode_response.status_code == 200:
                            geocode_data = geocode_response.json()
                            if geocode_data and len(geocode_data) > 0:
                                city_name = geocode_data[0].get("name", data.get("name", "Неизвестно"))
                    
                    # Если все еще нет названия, используем из weather API
                    if not city_name:
                        city_name = data.get("name", "Неизвестно")
                else:
                    # Если Nominatim не сработал, пробуем OpenWeatherMap Geocoding
                    geocode_url = f"http://api.openweathermap.org/geo/1.0/reverse?lat={latitude}&lon={longitude}&limit=1&appid={api_key}&lang=ru"
                    geocode_response = requests.get(geocode_url, timeout=10)
                    if geocode_response.status_code == 200:
                        geocode_data = geocode_response.json()
                        if geocode_data and len(geocode_data) > 0:
                            city_name = geocode_data[0].get("name", data.get("name", "Неизвестно"))
                        else:
                            city_name = data.get("name", "Неизвестно")
                    else:
                        city_name = data.get("name", "Неизвестно")
            except Exception as e:
                # Если все методы не сработали, используем название из weather API
                city_name = data.get("name", "Неизвестно")
            
            # Извлекаем данные из ответа
            temperature = data.get("main", {}).get("temp")
            weather_description = data.get("weather", [{}])[0].get("description", "нет данных")
            
            # Форматируем вывод
            print(f"Погода в {city_name} ({latitude}, {longitude}): {temperature}°C, {weather_description}")
            return data
        elif response.status_code == 401:
            print("Ошибка: Неверный API ключ. Проверьте файл .env")
            return None
        else:
            print(f"Ошибка: {response.status_code} - {response.text}")
            return None
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError, requests.exceptions.RequestException) as e:
        print(f"Ошибка: Не удалось получить данные о погоде. {type(e).__name__}")
        
        # Предлагаем использовать кэш
        cache_data = load_weather_cache()
        if cache_data:
            print("\nХотите посмотреть данные из кэша? (да/нет): ", end="")
            user_choice = input().strip().lower()
            if user_choice in ['да', 'yes', 'y', 'д']:
                format_cached_weather(cache_data)
                return cache_data.get("weather_data")
        else:
            print("Кэш недоступен или устарел (старше 3 часов).")
        return None

#погода по часам ---------------------------------------
def get_weather_by_hour(latitude: float, longitude: float) -> dict:
    
    api_key = os.getenv("API_KEY")
    
    if not api_key:
        print("Ошибка: API_KEY не установлен в переменных окружения!")
        env_path = BASE_DIR / '.env'
        print(f"Проверьте, что файл .env существует в директории: {BASE_DIR}")
        print(f"Файл должен содержать строку: API_KEY=ваш_ключ")
        return None
    
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={latitude}&lon={longitude}&appid={api_key}&units=metric&lang=ru"
    print(url) 
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            print(f"Ошибка: {response.status_code} - {response.text}")
            return None
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError, requests.exceptions.RequestException) as e:
        print(f"Ошибка: Не удалось получить данные о погоде. {type(e).__name__}")
        return None
#погода по часам --------------------------------------- end

#загрязнение воздуха ---------------------------------------
def get_pollutant_category(pollutant: str, value: float) -> tuple:
    """
    Определяет категорию качества воздуха для конкретного загрязняющего вещества.
    Возвращает (индекс, название категории).
    Согласно таблице: [ - включительно, ) - исключительно, > - больше, >= - больше или равно
    """
    # Определяем категории для каждого загрязнителя
    # Формат: (индекс, название, минимальное значение включительно, максимальное значение исключительно)
    if pollutant == "SO2":
        if 0 <= value < 20:
            return 1, "Good"
        elif 20 <= value < 80:
            return 2, "Fair"
        elif 80 <= value < 250:
            return 3, "Moderate"
        elif 250 <= value < 350:
            return 4, "Poor"
        elif value > 350:  # >350
            return 5, "Very Poor"
    
    elif pollutant == "NO2":
        if 0 <= value < 40:
            return 1, "Good"
        elif 40 <= value < 70:
            return 2, "Fair"
        elif 70 <= value < 150:
            return 3, "Moderate"
        elif 150 <= value < 200:
            return 4, "Poor"
        elif value >= 200:  # >=200
            return 5, "Very Poor"
    
    elif pollutant == "PM10":
        if 0 <= value < 20:
            return 1, "Good"
        elif 20 <= value < 50:
            return 2, "Fair"
        elif 50 <= value < 100:
            return 3, "Moderate"
        elif 100 <= value < 200:
            return 4, "Poor"
        elif value >= 200:  # >=200
            return 5, "Very Poor"
    
    elif pollutant == "PM2_5":
        if 0 <= value < 10:
            return 1, "Good"
        elif 10 <= value < 25:
            return 2, "Fair"
        elif 25 <= value < 50:
            return 3, "Moderate"
        elif 50 <= value < 75:
            return 4, "Poor"
        elif value > 75:  # >75
            return 5, "Very Poor"
    
    elif pollutant == "O3":
        if 0 <= value < 60:
            return 1, "Good"
        elif 60 <= value < 100:
            return 2, "Fair"
        elif 100 <= value < 140:
            return 3, "Moderate"
        elif 140 <= value < 180:
            return 4, "Poor"
        elif value > 180:  # >180
            return 5, "Very Poor"
    
    elif pollutant == "CO":
        if 0 <= value < 4400:
            return 1, "Good"
        elif 4400 <= value < 9400:
            return 2, "Fair"
        elif 9400 <= value < 12400:
            return 3, "Moderate"
        elif 12400 <= value < 15400:
            return 4, "Poor"
        elif value > 15400:  # >15400
            return 5, "Very Poor"
    
    return 1, "Good"  # По умолчанию


def format_pollution_data(data: dict) -> None:
    """
    Форматирует и выводит данные о загрязнении воздуха с анализом по таблице.
    """
    if not data or "list" not in data or not data["list"]:
        print("Ошибка: некорректные данные о загрязнении воздуха")
        return
    
    # Получаем последние данные (текущие)
    current_data = data["list"][0]
    components = current_data.get("components", {})
    main_index = current_data.get("main", {}).get("aqi", 1)  # AQI от API (1-5)
    
    # Названия загрязняющих веществ на русском
    pollutant_names = {
        "SO2": "Диоксид серы (SO₂)",
        "NO2": "Диоксид азота (NO₂)",
        "PM10": "Взвешенные частицы PM₁₀",
        "PM2_5": "Взвешенные частицы PM₂.₅",
        "O3": "Озон (O₃)",
        "CO": "Оксид углерода (CO)"
    }
    
    # Анализируем каждый загрязнитель
    # API возвращает ключи в нижнем регистре, нужно преобразовать
    pollutant_mapping = {
        "so2": "SO2",
        "no2": "NO2",
        "pm10": "PM10",
        "pm2_5": "PM2_5",
        "o3": "O3",
        "co": "CO"
    }
    
    pollutant_analysis = {}
    max_category_index = 1
    max_category_name = "Good"
    
    for api_key, value in components.items():
        # Преобразуем ключ API в наш формат
        pollutant = pollutant_mapping.get(api_key.lower(), api_key.upper())
        
        if pollutant in pollutant_names:
            index, category = get_pollutant_category(pollutant, value)
            pollutant_analysis[pollutant] = {
                "value": value,
                "index": index,
                "category": category,
                "name": pollutant_names[pollutant]
            }
            if index > max_category_index:
                max_category_index = index
                max_category_name = category
    
    # Категории на русском
    category_names_ru = {
        "Good": "Хорошее",
        "Fair": "Удовлетворительное",
        "Moderate": "Умеренное",
        "Poor": "Плохое",
        "Very Poor": "Очень плохое"
    }
    
    # Выводим общий статус
    print(f"\n{'='*70}")
    print(f"КАЧЕСТВО ВОЗДУХА")
    print(f"{'='*70}")
    print(f"Общий статус: {category_names_ru.get(max_category_name, max_category_name)} (Индекс: {max_category_index})")
    print(f"{'='*70}\n")
    
    # Выводим детальную информацию
    print("Детальная информация по загрязняющим веществам:\n")
    
    # Разделяем на превышающие норму и в норме
    above_norm = []
    within_norm = []
    
    for pollutant, info in pollutant_analysis.items():
        status = {
            "name": info["name"],
            "value": info["value"],
            "category": info["category"],
            "index": info["index"]
        }
        if info["index"] >= 3:  # Moderate и выше считаем превышением нормы
            above_norm.append(status)
        else:
            within_norm.append(status)
    
    # Выводим превышающие норму
    if above_norm:
        print("⚠️  ПРЕВЫШЕНИЕ НОРМЫ:")
        print("-" * 70)
        for item in sorted(above_norm, key=lambda x: x["index"], reverse=True):
            category_ru = category_names_ru.get(item["category"], item["category"])
            unit = "µg/m³" if item["name"] != "Оксид углерода (CO)" else "µg/m³"
            print(f"  • {item['name']}: {item['value']:.2f} {unit}")
            print(f"    Категория: {category_ru} (Индекс: {item['index']})")
        print()
    
    # Выводим в пределах нормы
    if within_norm:
        print("✅ В ПРЕДЕЛАХ НОРМЫ:")
        print("-" * 70)
        for item in sorted(within_norm, key=lambda x: x["index"]):
            category_ru = category_names_ru.get(item["category"], item["category"])
            unit = "µg/m³" if item["name"] != "Оксид углерода (CO)" else "µg/m³"
            print(f"  • {item['name']}: {item['value']:.2f} {unit}")
            print(f"    Категория: {category_ru} (Индекс: {item['index']})")
        print()
    
    # Выводим время измерения
    dt = current_data.get("dt")
    if dt:
        try:
            dt_obj = datetime.fromtimestamp(dt)
            print(f"Время измерения: {dt_obj.strftime('%d.%m.%Y %H:%M:%S')}")
        except:
            pass


def get_weather_pollution(latitude: float, longitude: float) -> dict:
    """
    Получает данные о загрязнении воздуха по координатам.
    """
    api_key = os.getenv("API_KEY")
    
    if not api_key:
        print("Ошибка: API_KEY не установлен в переменных окружения!")
        env_path = BASE_DIR / '.env'
        print(f"Проверьте, что файл .env существует в директории: {BASE_DIR}")
        print(f"Файл должен содержать строку: API_KEY=ваш_ключ")
        return None
    
    url = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={latitude}&lon={longitude}&appid={api_key}"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # Форматируем и выводим данные
            format_pollution_data(data)
            return data
        else:
            print(f"Ошибка: {response.status_code} - {response.text}")
            return None
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError, requests.exceptions.RequestException) as e:
        print(f"Ошибка: Не удалось получить данные о загрязнении воздуха. {type(e).__name__}")
        return None
#загрязнение воздуха --------------------------------------- end

if __name__ == "__main__":
    print("=== Программа погоды ===")
    choice = input("Выберите опцию:\n1 - Погода по городу\n2 - Погода по координатам\n3 - Прогноз погоды по часам\n4 - Загрязнение воздуха\nВаш выбор: ")
    
    if choice == "1":
        city = input("Введите название города: ")
        if city:
            get_weather(city=city)
        else:
            print("Город не указан!")
    
    elif choice == "2":
        try:
            latitude = float(input("Введите широту (latitude): "))
            longitude = float(input("Введите долготу (longitude): "))
            get_weather_by_coordinates(latitude, longitude)
             
        except ValueError:
            print("Ошибка: введите корректные числовые значения для координат!")
    
    elif choice == "3":                   
        try:
            latitude = float(input("Введите широту (latitude): "))
            longitude = float(input("Введите долготу (longitude): "))
            get_weather_by_hour(latitude=latitude, longitude=longitude)
        except ValueError:
            print("Ошибка: введите корректные числовые значения для координат!")
    
    elif choice == "4":
        try:
            latitude = float(input("Введите широту (latitude): "))
            longitude = float(input("Введите долготу (longitude): "))
            get_weather_pollution(latitude=latitude, longitude=longitude)
        except ValueError:
            print("Ошибка: введите корректные числовые значения для координат!")
    
    else:
        print("Неверный выбор!")