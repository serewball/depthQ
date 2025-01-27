import pandas as pd
import os

class CropService:
    def __init__(self):
        # 读取作物推荐数据集
        file_path = os.path.join('作物需求', 'Crop-Recommendation', 'Crop_Recommendation.csv')
        self.crop_data = pd.read_csv(file_path)
        
        # 获取所有可用作物类型
        self.available_crops = self.crop_data['Crop'].unique()  # 使用正确的列名 'Crop'
        
    def get_crop_recommendations(self, temperature, humidity, nitrogen=None, phosphorus=None, potassium=None, ph=None, rainfall=None):
        """基于环境条件获取作物建议"""
        try:
            conditions = []
            
            # 添加必要的条件（温度和湿度）
            conditions.append(self.crop_data['Temperature'].between(temperature-5, temperature+5))
            conditions.append(self.crop_data['Humidity'].between(humidity-10, humidity+10))
            
            # 添加可选条件
            if nitrogen is not None:
                conditions.append(self.crop_data['Nitrogen'].between(nitrogen-10, nitrogen+10))
            if phosphorus is not None:
                conditions.append(self.crop_data['Phosphorus'].between(phosphorus-10, phosphorus+10))
            if potassium is not None:
                conditions.append(self.crop_data['Potassium'].between(potassium-10, potassium+10))
            if ph is not None:
                conditions.append(self.crop_data['pH_Value'].between(ph-0.5, ph+0.5))
            if rainfall is not None:
                conditions.append(self.crop_data['Rainfall'].between(rainfall-200, rainfall+200))
            
            final_condition = conditions[0]
            for condition in conditions[1:]:
                final_condition = final_condition & condition
            
            suitable_crops = self.crop_data[final_condition]
            
            recommendations = []
            for _, crop in suitable_crops.iterrows():
                recommendations.append({
                    'name': crop['Crop'],
                    'optimal_conditions': {
                        'temperature': crop['Temperature'],
                        'humidity': crop['Humidity'],
                        'nitrogen': crop['Nitrogen'],
                        'phosphorus': crop['Phosphorus'],
                        'potassium': crop['Potassium'],
                        'ph': crop['pH_Value'],
                        'rainfall': crop['Rainfall']
                    }
                })
            return recommendations
            
        except Exception as e:
            print(f"推荐作物时出错: {e}")
            return []
    
    def get_irrigation_schedule(self, crop_name, weather_data):
        """生成灌溉计划"""
        try:
            # 获取作物的最佳条件
            crop_info = self.crop_data[self.crop_data['Crop'] == crop_name].iloc[0]
            
            # 获取当前天气条件
            current_temp = weather_data['main']['temp']
            current_humidity = weather_data['main']['humidity']
            current_rainfall = weather_data.get('rain', {}).get('1h', 0) * 24
            
            # 计算需水量
            optimal_rainfall = crop_info['Rainfall'] / 365
            water_deficit = max(0, optimal_rainfall - current_rainfall)
            
            # 基于温度和湿度调整灌溉建议
            temp_factor = 1 + max(0, (current_temp - crop_info['Temperature']) / 10)
            humidity_factor = 1 - (current_humidity - crop_info['Humidity']) / 100
            
            adjusted_water_need = water_deficit * temp_factor * humidity_factor
            
            irrigation_plan = {
                'crop_name': crop_name,
                'current_conditions': {
                    'temperature': current_temp,
                    'humidity': current_humidity,
                    'daily_rainfall': current_rainfall
                },
                'optimal_conditions': {
                    'temperature': crop_info['Temperature'],
                    'humidity': crop_info['Humidity'],
                    'daily_rainfall': optimal_rainfall
                },
                'irrigation_recommendation': {
                    'need_irrigation': adjusted_water_need > 0,
                    'water_amount': round(adjusted_water_need, 2),
                    'unit': 'mm',
                    'schedule': self._get_irrigation_timing(current_temp, current_humidity)
                }
            }
            
            return irrigation_plan
            
        except Exception as e:
            print(f"生成灌溉计划时出错: {e}")
            return None
    
    def _get_irrigation_timing(self, temperature, humidity):
        """根据温度和湿度确定最佳灌溉时间"""
        if temperature > 30:
            return "建议在清晨或傍晚进行灌溉，避免水分蒸发"
        elif humidity < 40:
            return "建议分多次少量灌溉，避免水分快速流失"
        else:
            return "建议在上午进行灌溉，保证作物充分吸收" 