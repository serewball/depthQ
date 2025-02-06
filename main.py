from backend.services.weather_service import WeatherService
from backend.services.crop_service import CropService
from backend.services.visualization_service import VisualizationService
from datetime import datetime
import os
import pandas as pd

# 定义几个适合农作物生长的地点
LOCATIONS = {
    '三亚': (18.2528, 109.5127),
    '广州': (23.1291, 113.2644),
    '昆明': (24.8801, 102.8329),
    '海口': (20.0442, 110.1995),
    '南宁': (22.8170, 108.3665)
}

def main():
    # 初始化服务
    weather_service = WeatherService()
    crop_service = CropService()
    vis_service = VisualizationService()
    
    print(f"当前工作目录: {os.getcwd()}")
    
    # 选择地点（这里使用三亚作为示例）
    location_name = '广州'
    lat, lon = LOCATIONS[location_name]
    
    # 获取天气数据
    print(f"\n获取{location_name}的天气数据...")
    weather_data = weather_service.get_weather_data(lat, lon)
    
    if weather_data:
        print(f"\n=== {location_name}当前天气数据 ===")
        print(f"位置: {weather_data['location']['name']}, {weather_data['location']['country']}")
        print(f"天气: {weather_data['weather']['description']}")
        print(f"温度: {weather_data['main']['temp']}°C")
        print(f"湿度: {weather_data['main']['humidity']}%")
        print(f"气压: {weather_data['main']['pressure']}hPa")
        print(f"降雨量: {weather_data['rain'].get('1h', 0)}mm/h")
        print(f"风速: {weather_data['wind']['speed']}m/s")
        
        # 收集作物状态数据
        crop_status_data = []
        
        # 获取所有作物数据并生成状态记录
        print("\n=== 生成所有作物的状态记录 ===")
        for _, crop in crop_service.crop_data.iterrows(): 
            crop_name = crop['Crop']
            # print(f"正在生成 {crop_name} 的状态记录...")
            
            # 收集作物状态数据
            crop_status_data.append({
                '作物名': crop_name,
                '当前温度(°C)': weather_data['main']['temp'],
                '当前湿度(%)': weather_data['main']['humidity'],
                '当前日降雨量(mm)': weather_data.get('rain', {}).get('1h', 0) * 24,
                '最佳温度(°C)': crop['Temperature'],
                '最佳湿度(%)': crop['Humidity'],
                '最佳日降雨量(mm)': crop['Rainfall'] / 365
            })
        
        # 将作物状态数据保存到 Excel 文件
        crop_status_df = pd.DataFrame(crop_status_data)
        status_file_path = os.path.join("D:\\py\\output\\images", f"作物状态记录{location_name}.xlsx")
        crop_status_df.to_excel(status_file_path, index=False)
        print(f"作物状态记录已保存至: {status_file_path}")
        
        # 获取作物推荐
        recommendations = crop_service.get_crop_recommendations(
            temperature=weather_data['main']['temp'],
            humidity=weather_data['main']['humidity'],
            nitrogen=50,
            phosphorus=50,
            potassium=50,
            ph=6.5,
            rainfall=200
        )
        
        # 显示推荐结果
        print("\n=== 推荐种植的作物 ===")
        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}. {rec['name']} (匹配度: {rec['match_score']:.1f}%)")
            print("最佳生长条件:")
            conditions = rec['optimal_conditions']
            print(f"  温度: {conditions['temperature']}°C")
            print(f"  湿度: {conditions['humidity']}%")
            print(f"  氮含量: {conditions['nitrogen']}")
            print(f"  磷含量: {conditions['phosphorus']}")
            print(f"  钾含量: {conditions['potassium']}")
            print(f"  pH值: {conditions['ph']}")
            print(f"  年降雨量: {conditions['rainfall']}mm")
            
            # 生成灌溉建议
            irrigation_advice = (
                f"作物: {rec['name']}\n"
                f"最佳生长条件:\n"
                f"  温度: {conditions['temperature']}°C\n"
                f"  湿度: {conditions['humidity']}%\n"
                f"  氮含量: {conditions['nitrogen']}\n"
                f"  磷含量: {conditions['phosphorus']}\n"
                f"  钾含量: {conditions['potassium']}\n"
                f"  pH值: {conditions['ph']}\n"
                f"  年降雨量: {conditions['rainfall']}mm\n"
                f"灌溉建议: 根据当前条件，建议灌溉量为 {rec['optimal_conditions']['rainfall'] / 365:.2f} mm。\n"
            )
            
            # 写入文本文件
            advice_file_path = os.path.join("D:\\py\\output\\images", f"{rec['name']}灌溉建议.txt")
            with open(advice_file_path, 'w', encoding='utf-8') as f:
                f.write(irrigation_advice)
            print(f"灌溉建议已保存至: {advice_file_path}")
        
        # 测试灌溉计划
        if recommendations:
            try:  # 添加错误处理
                first_crop = recommendations[0]['name']
                print(f"\n正在为 {first_crop} 生成灌溉计划...")
                
                irrigation_plan = crop_service.get_irrigation_schedule(first_crop, weather_data)
                
                if irrigation_plan:
                    # 记录灌溉历史
                    vis_service.add_irrigation_record(
                        datetime.now(),
                        irrigation_plan['crop_name'],
                        irrigation_plan['irrigation_recommendation']['water_amount'],
                        irrigation_plan['current_conditions']
                    )
                    
                    # 生成灌溉历史的 Excel 文件
                    irrigation_history_df = vis_service.get_irrigation_history_df(irrigation_plan['crop_name'])
                    history_file_path = os.path.join("D:\\py\\output\\images", f"{first_crop}灌溉历史.xlsx")
                    irrigation_history_df.to_excel(history_file_path, index=False)
                    print(f"灌溉历史已保存至: {history_file_path}")
                    
                    print("\n=== 灌溉计划 ===")
                    print(f"作物: {irrigation_plan['crop_name']}")
                    
                    print("\n正在生成可视化图表...")
                    # 记录并可视化当前状态
                    vis_service.plot_current_status(
                        {'name': irrigation_plan['crop_name']},
                        irrigation_plan['current_conditions'],
                        irrigation_plan['optimal_conditions']
                    )
                    
                    # 绘制历史记录
                    vis_service.plot_irrigation_history()
                    
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
                    
                    print("\n=== 模型信息 ===")
                    model_info = irrigation_plan['model_info']
                    try:
                        print(f"当前探索率 (epsilon): {model_info.get('epsilon', 0):.4f}")
                        print(f"本次决策奖励: {model_info.get('reward', 0):.2f}")
                    except Exception as e:
                        print(f"显示模型信息时出错: {e}")
            except Exception as e:
                print(f"生成灌溉计划时出错: {e}")
    
    print("\n智慧灌溉系统运行完成")
    
    # 检查图片是否生成
    output_dir = os.path.join(os.getcwd(), 'output', 'images')
    if os.path.exists(output_dir):
        print(f"\n输出目录 {output_dir} 中的文件:")
        for file in os.listdir(output_dir):
            print(f"- {file}")
    else:
        print(f"\n输出目录 {output_dir} 不存在")

if __name__ == "__main__":
    main() 