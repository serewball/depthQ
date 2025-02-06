import requests
from ..config.config import Config

class WeatherService:
    def __init__(self):
        self.api_key = Config.WEATHER_API_KEY
        self.api_url = "https://api.openweathermap.org/data/2.5/weather"  # 修改为正确的API端点
    
    def get_weather_data(self, latitude, longitude):
        """获取指定位置的天气数据"""
        params = {
            'lat': latitude,
            'lon': longitude,
            'appid': self.api_key,
            'units': 'metric',  # 使用摄氏度
            'lang': 'zh_cn'     # 使用中文返回结果
        }
        
        try:
            print(f"正在获取天气数据...")
            response = requests.get(self.api_url, params=params)
            response.raise_for_status()
            
            weather_data = response.json()
            print("天气数据获取成功")
            
            # 格式化天气数据
            formatted_data = {
                'main': {
                    'temp': weather_data['main']['temp'],
                    'humidity': weather_data['main']['humidity'],
                    'pressure': weather_data['main']['pressure']
                },
                'rain': weather_data.get('rain', {'1h': 0}),  # 如果没有降雨数据，默认为0
                'wind': weather_data['wind'],
                'weather': weather_data['weather'][0],
                'location': {
                    'name': weather_data.get('name', 'Unknown'),
                    'country': weather_data.get('sys', {}).get('country', 'Unknown')
                }
            }
            
            return formatted_data
            
        except requests.exceptions.RequestException as e:
            print(f"获取天气数据失败: {e}")
            print(f"详细错误信息: {getattr(e.response, 'text', '')}")
            return None 