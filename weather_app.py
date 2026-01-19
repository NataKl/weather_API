import requests
from dotenv import load_dotenv 
import os
from urllib.parse import quote
from pathlib import Path
import json
from datetime import datetime, timedelta

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
        
        # Форматируем вывод
        if city:
            print(f"Погода в {city_name}: {temperature}°C, {weather_description}")
        elif lat is not None and lon is not None:
            print(f"Погода в координатах ({lat}, {lon}): {temperature}°C, {weather_description}")
        
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
                
                # Форматируем вывод
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
            
            # Извлекаем данные из ответа
            temperature = data.get("main", {}).get("temp")
            weather_description = data.get("weather", [{}])[0].get("description", "нет данных")
            city_name = data.get("name", "Неизвестно")
            
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


if __name__ == "__main__":
    print("=== Программа погоды ===")
    choice = input("Выберите опцию:\n1 - Погода по городу\n2 - Погода по координатам\nВаш выбор: ")
    
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
    
    else:
        print("Неверный выбор!")