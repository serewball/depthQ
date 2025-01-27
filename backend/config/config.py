# 配置文件
class Config:
    # OpenWeatherMap API配置
    WEATHER_API_KEY = "你的API密钥"
    WEATHER_API_URL = "http://api.openweathermap.org/data/2.5/weather"
    
    # 数据库配置
    DATABASE_URL = "sqlite:///irrigation_system.db"
    
    # 系统配置
    DEBUG = True
    SECRET_KEY = "your-secret-key" 