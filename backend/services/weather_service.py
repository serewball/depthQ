import requests
from ..config.config import Config

class WeatherService:
    def __init__(self):
        self.api_key = Config.WEATHER_API_KEY
        self.api_url = Config.WEATHER_API_URL
    
    def get_weather_data(self, latitude, longitude):
        """获取指定位置的天气数据"""
        params = {
            'lat': latitude,
            'lon': longitude,
            'appid': self.api_key,
            'units': 'metric'
        }
        
        try:
            response = requests.get(self.api_url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"获取天气数据失败: {e}")
            return None 