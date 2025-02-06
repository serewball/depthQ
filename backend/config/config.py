# 配置文件
class Config:
    # OpenWeatherMap API配置
    WEATHER_API_KEY = "93625251f33ce2e39dea5a9f1e110c92"  # OpenWeatherMap API密钥
    WEATHER_API_URL = "http://api.openweathermap.org/data/2.5/forecast/city?APPID=93625251f33ce2e39dea5a9f1e110c92"  # 使用 HTTPS
    
    # 数据库配置
    DATABASE_URL = "sqlite:///irrigation_system.db"
    
    # 系统配置
    DEBUG = True
    SECRET_KEY = "your-secret-key" 