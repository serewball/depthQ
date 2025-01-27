from backend.services.weather_service import WeatherService
from backend.services.crop_service import CropService

def main():
    # 初始化服务
    weather_service = WeatherService()
    crop_service = CropService()
    
    # 测试天气服务
    weather_data = weather_service.get_weather_data(39.9042, 116.4074)  # 北京坐标
    if weather_data:
        print("\n=== 当前天气数据 ===")
        print(f"温度: {weather_data['main']['temp']}°C")
        print(f"湿度: {weather_data['main']['humidity']}%")
        
        # 测试作物推荐
        recommendations = crop_service.get_crop_recommendations(
            temperature=weather_data['main']['temp'],
            humidity=weather_data['main']['humidity'],
            nitrogen=50,  # 示例值
            phosphorus=50,  # 示例值
            potassium=50,  # 示例值
            ph=6.5,  # 示例值
            rainfall=200  # 示例值
        )
        
        print("\n=== 推荐种植的作物 ===")
        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}. {rec['name']}")
            print("最佳生长条件:")
            conditions = rec['optimal_conditions']
            print(f"  温度: {conditions['temperature']}°C")
            print(f"  湿度: {conditions['humidity']}%")
            print(f"  降雨量: {conditions['rainfall']}mm")
        
        # 测试灌溉计划
        if recommendations:
            first_crop = recommendations[0]['name']
            irrigation_plan = crop_service.get_irrigation_schedule(first_crop, weather_data)
            
            print("\n=== 灌溉计划 ===")
            if irrigation_plan:
                print(f"作物: {irrigation_plan['crop_name']}")
                print("\n当前条件:")
                current = irrigation_plan['current_conditions']
                print(f"  温度: {current['temperature']}°C")
                print(f"  湿度: {current['humidity']}%")
                print(f"  日降雨量: {current['daily_rainfall']}mm")
                
                print("\n灌溉建议:")
                rec = irrigation_plan['irrigation_recommendation']
                print(f"  需要灌溉: {'是' if rec['need_irrigation'] else '否'}")
                print(f"  建议用水量: {rec['water_amount']}{rec['unit']}")
                print(f"  灌溉时间: {rec['schedule']}")
    
    print("\n智慧灌溉系统运行完成")

if __name__ == "__main__":
    main() 