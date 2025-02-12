import pandas as pd
import os
from ..models.dqn_model import DQNAgent

class CropService:
    def __init__(self):
        try:
            # 读取作物推荐数据集
            file_path = os.path.join('作物需求', 'Crop-Recommendation', 'Crop_Recommendation.csv')
            print(f"尝试读取数据文件: {file_path}")
            self.crop_data = pd.read_csv(file_path)
            print("数据集读取成功")
            print(f"数据集包含 {len(self.crop_data)} 条记录")
            print("数据集列名:", self.crop_data.columns.tolist())
            
            # 获取所有可用作物类型
            self.available_crops = self.crop_data['Crop'].unique()
            print("可用作物类型:", self.available_crops)
            
            # 初始化DQN代理
            self.state_size = 6  # 状态空间大小
            self.action_size = 10  # 灌溉量级别数量
            self.dqn_agent = DQNAgent(self.state_size, self.action_size)
            self.decision_count = 0
            
            # 可以修改温度阈值
            self.TEMPERATURE_THRESHOLDS = {
                'high': 30,
                'medium': 25
            }
            
            # 或湿度判断范围
            self.HUMIDITY_RANGES = {
                'low': 50,
                'high': 70
            }
            
        except Exception as e:
            print(f"初始化CropService时出错: {e}")
            raise
    
    def get_crop_recommendations(self, temperature, humidity, nitrogen=None, phosphorus=None, potassium=None, ph=None, rainfall=None):
        """基于环境条件获取作物建议"""
        try:
            print("\n开始作物推荐...")
            print(f"输入条件: 温度={temperature}°C, 湿度={humidity}%")
            
            conditions = []
            
            # 放宽温度和湿度的匹配范围
            conditions.append(self.crop_data['Temperature'].between(temperature-10, temperature+10))  # 温度范围改为±10°C
            conditions.append(self.crop_data['Humidity'].between(humidity-20, humidity+20))  # 湿度范围改为±20%
            
            # 放宽其他条件的匹配范围
            if nitrogen is not None:
                conditions.append(self.crop_data['Nitrogen'].between(nitrogen-20, nitrogen+20))  # 范围改为±20
            if phosphorus is not None:
                conditions.append(self.crop_data['Phosphorus'].between(phosphorus-20, phosphorus+20))  # 范围改为±20
            if potassium is not None:
                conditions.append(self.crop_data['Potassium'].between(potassium-20, potassium+20))  # 范围改为±20
            if ph is not None:
                conditions.append(self.crop_data['pH_Value'].between(ph-1.0, ph+1.0))  # pH范围改为±1.0
            if rainfall is not None:
                conditions.append(self.crop_data['Rainfall'].between(rainfall-500, rainfall+500))  # 降雨量范围改为±500mm
            
            # 组合所有条件
            final_condition = conditions[0]
            for condition in conditions[1:]:
                final_condition = final_condition & condition
            
            # 获取符合条件的作物
            suitable_crops = self.crop_data[final_condition]
            print(f"找到 {len(suitable_crops)} 个符合条件的作物")
            
            # 如果没有完全匹配的作物，尝试只用温度和湿度条件
            if len(suitable_crops) == 0:
                print("使用宽松条件重新搜索...")
                conditions = [
                    self.crop_data['Temperature'].between(temperature-15, temperature+15),  # 更宽松的温度范围
                    self.crop_data['Humidity'].between(humidity-30, humidity+30)  # 更宽松的湿度范围
                ]
                final_condition = conditions[0] & conditions[1]
                suitable_crops = self.crop_data[final_condition]
                print(f"使用宽松条件找到 {len(suitable_crops)} 个作物")
            
            # 构建推荐列表，并按照条件匹配度排序
            recommendations = []
            for _, crop in suitable_crops.iterrows():
                # 计算匹配度分数
                temp_diff = abs(crop['Temperature'] - temperature)
                humidity_diff = abs(crop['Humidity'] - humidity)
                match_score = 100 - (temp_diff * 2 + humidity_diff * 0.5)  # 简单的评分机制
                
                recommendations.append({
                    'name': crop['Crop'],
                    'match_score': match_score,
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
            
            # 按匹配度排序
            recommendations.sort(key=lambda x: x['match_score'], reverse=True)
            
            # 只返回前5个最佳匹配
            recommendations = recommendations[:5]
            print(f"生成了 {len(recommendations)} 个作物推荐")
            
            return recommendations
            
        except Exception as e:
            print(f"推荐作物时出错: {e}")
            return []
    
    def get_irrigation_schedule(self, crop_name, weather_data):
        """使用DQN生成灌溉计划"""
        try:
            # 获取作物信息
            crop_info = self.crop_data[self.crop_data['Crop'] == crop_name].iloc[0]
            
            # 构建当前状态
            current_state = self.dqn_agent.get_state(weather_data, crop_info)
            
            # 获取DQN推荐的动作
            action = self.dqn_agent.get_action(current_state)
            
            # 将动作转换为实际的灌溉量（例如：0-9对应0-45mm的灌溉量）
            water_amount = action * 5  # 每个级别间隔5mm
            
            # 计算奖励（这是一个简单的奖励函数示例）
            reward = self._calculate_reward(water_amount, weather_data, crop_info)
            
            # 模拟执行灌溉后的下一个状态
            next_state = self._simulate_next_state(current_state, water_amount)
            
            # 存储经验用于训练
            self.dqn_agent.remember(current_state, action, reward, next_state, False)
            
            # 训练模型
            self.dqn_agent.train()
            
            # 每100次决策更新一次目标网络
            if self.decision_count % 100 == 0:
                self.dqn_agent.update_target_network()
            self.decision_count += 1
            
            # 构建灌溉计划
            irrigation_plan = {
                'crop_name': crop_name,
                'current_conditions': {
                    'temperature': weather_data['main']['temp'],
                    'humidity': weather_data['main']['humidity'],
                    'daily_rainfall': weather_data.get('rain', {}).get('1h', 0) * 24
                },
                'optimal_conditions': {
                    'temperature': crop_info['Temperature'],
                    'humidity': crop_info['Humidity'],
                    'daily_rainfall': crop_info['Rainfall'] / 365
                },
                'irrigation_recommendation': {
                    'need_irrigation': water_amount > 0,
                    'water_amount': water_amount,
                    'unit': 'mm',
                    'schedule': self._get_irrigation_timing(
                        weather_data['main']['temp'],
                        weather_data['main']['humidity']
                    )
                },
                'model_info': {
                    'epsilon': self.dqn_agent.epsilon,
                    'reward': reward
                }
            }
            
            return irrigation_plan
            
        except Exception as e:
            print(f"生成灌溉计划时出错: {e}")
            import traceback
            print(traceback.format_exc())
            return None
    
    def _calculate_reward(self, water_amount, weather_data, crop_info):
        """计算灌溉决策的奖励"""
        # 获取当前条件
        current_temp = weather_data['main']['temp']
        current_humidity = weather_data['main']['humidity']
        current_rainfall = weather_data.get('rain', {}).get('1h', 0) * 24
        
        # 计算理想日需水量
        optimal_daily_water = crop_info['Rainfall'] / 365
        
        # 计算总供水量（降雨 + 灌溉）
        total_water = current_rainfall + water_amount
        
        # 计算各项指标的奖励
        water_reward = -abs(total_water - optimal_daily_water) / optimal_daily_water * 50
        temp_reward = -abs(current_temp - crop_info['Temperature']) / crop_info['Temperature'] * 30
        humidity_reward = -abs(current_humidity - crop_info['Humidity']) / crop_info['Humidity'] * 20
        
        # 节水奖励
        water_saving = 0 if water_amount == 0 else -water_amount * 0.1
        
        # 总奖励
        total_reward = water_reward + temp_reward + humidity_reward + water_saving
        
        # 添加额外的惩罚
        if total_water < optimal_daily_water * 0.5:  # 水分严重不足
            total_reward -= 100
        elif total_water > optimal_daily_water * 1.5:  # 水分过多
            total_reward -= 100
        
        return total_reward
    
    def _simulate_next_state(self, current_state, water_amount):
        """模拟灌溉后的状态"""
        next_state = current_state.copy()
        # 模拟灌溉对湿度的影响
        humidity_increase = water_amount * 0.5  # 假设每1mm水增加0.5%的湿度
        next_state[1] = min(100, next_state[1] + humidity_increase)  # 湿度不超过100%
        return next_state
    
    def _get_irrigation_timing(self, temperature, humidity):
        """生成灌溉时间建议"""
        try:
            # 温度判断标准（从高温到低温排序）
            temp_thresholds = [
                (35, "凌晨（4:00-6:00）"),  # 高温时选择凌晨
                (30, "清晨（5:00-7:00）"),  # 较高温选择清晨
                (25, "傍晚（17:00-19:00）"),  # 中等温度选择傍晚
                (20, "早晨（6:00-8:00）"),   # 较低温选择早晨
                (float('-inf'), "上午（8:00-10:00）")  # 低温时可以选择上午
            ]
            
            # 湿度判断标准
            humidity_ranges = [
                (80, "建议待湿度降低后再灌溉"),  # 湿度过高
                (70, "建议分2次少量灌溉"),      # 湿度较高
                (60, "建议正常灌溉"),          # 适中湿度
                (40, "建议适当增加灌溉量"),     # 湿度较低
                (float('-inf'), "建议多次少量灌溉")  # 湿度过低
            ]
            
            # 查找温度建议
            time_suggestion = None
            for threshold, suggestion in temp_thresholds:
                if temperature >= threshold:
                    time_suggestion = suggestion
                    break
                
            # 查找湿度建议
            freq_suggestion = None
            for threshold, suggestion in humidity_ranges:
                if humidity >= threshold:
                    freq_suggestion = suggestion
                    break
                
            # 组合建议
            detailed_advice = f"{time_suggestion}，{freq_suggestion}"
            
            # 特殊条件处理
            if temperature > 35 and humidity < 40:
                detailed_advice += "（注意防止水分蒸发）"
            elif temperature < 10:
                detailed_advice += "（建议使用温水灌溉）"
            elif humidity > 85:
                detailed_advice = "当前湿度过高，建议暂缓灌溉"
            
            return detailed_advice
            
        except Exception as e:
            print(f"生成灌溉时间建议时出错: {e}")
            return "建议时间：根据当前条件无法提供具体建议"
    
    def get_optimal_conditions(self, current_state):
        # 预测建议
        adjustments = self.dqn_agent.predict(current_state)
        
        # 模拟执行建议后的新状态
        new_temp = current_state[0] + adjustments[0]
        new_humidity = current_state[1] + adjustments[1]
        new_rainfall = current_state[2] + adjustments[2]
        
        # 计算奖励值（基于与最佳条件的接近程度）
        reward = self._calculate_reward(new_temp, new_humidity, new_rainfall)
        
        # 更新模型
        self.dqn_agent.update_model(
            state=current_state,
            action=adjustments,
            reward=reward,
            next_state=[new_temp, new_humidity, new_rainfall]
        )
        
        return adjustments

    def generate_crop_status(self, weather_data):
        """生成作物状态记录并返回DataFrame"""
        status_data = []
        
        # 按作物类型分组处理
        grouped = self.crop_data.groupby('Crop')
        for crop_name, group in grouped:
            # 计算该作物的平均最佳条件
            avg_conditions = group.mean(numeric_only=True)
            
            # 构建当前状态
            current_state = self.dqn_agent.get_state(
                weather_data, 
                {
                    'Temperature': avg_conditions['Temperature'],
                    'Humidity': avg_conditions['Humidity'],
                    'Rainfall': avg_conditions['Rainfall']
                }
            )
            
            # 获取DQN建议
            action = self.dqn_agent.get_action(current_state)
            water_amount = action * 5  # 每个动作对应5mm灌溉量
            
            status_data.append({
                '作物名': crop_name,
                '当前温度': weather_data['main']['temp'],
                '当前湿度': weather_data['main']['humidity'],
                '当前日降雨量': weather_data.get('rain', {}).get('1h', 0) * 24,
                '最佳温度': avg_conditions['Temperature'],
                '最佳湿度': avg_conditions['Humidity'],
                '最佳日降雨量': avg_conditions['Rainfall'] / 365,
                '建议灌溉量': water_amount,
                '匹配度评分': self._calculate_match_score(weather_data, avg_conditions)
            })
        
        return pd.DataFrame(status_data)

    def _calculate_match_score(self, weather_data, crop_conditions):
        """
        计算当前条件与最佳条件的匹配度评分（0-100）
        """
        try:
            # 获取当前环境数据
            current_temp = weather_data['main']['temp']
            current_humidity = weather_data['main']['humidity']
            current_rainfall = weather_data.get('rain', {}).get('1h', 0) * 24  # 转换为日降雨量
            
            # 获取最佳条件
            optimal_temp = crop_conditions['Temperature']
            optimal_humidity = crop_conditions['Humidity']
            optimal_rainfall = crop_conditions['Rainfall'] / 365  # 年降雨转日降雨
            
            # 计算各项差异（使用相对误差）
            temp_diff = abs(current_temp - optimal_temp) / optimal_temp
            humidity_diff = abs(current_humidity - optimal_humidity) / optimal_humidity
            rainfall_diff = abs(current_rainfall - optimal_rainfall) / optimal_rainfall if optimal_rainfall != 0 else 0
            
            # 计算基础评分（100分制）
            base_score = 100 - (
                temp_diff * 40 +  # 温度占40%权重
                humidity_diff * 30 +  # 湿度占30%权重
                rainfall_diff * 30  # 降雨量占30%权重
            )
            
            # 确保评分在合理范围内
            final_score = max(0, min(100, base_score))
            
            # 添加额外修正（当所有条件都接近最佳值时给予奖励分）
            if temp_diff < 0.05 and humidity_diff < 0.05 and rainfall_diff < 0.1:
                final_score = min(100, final_score + 5)
                
            return round(final_score, 1)
            
        except KeyError as e:
            print(f"计算匹配度时缺少必要字段: {e}")
            return 0
        except ZeroDivisionError:
            print("警告：最佳条件中存在0值，可能导致计算异常")
            return 0

    def get_irrigation_advice(self, crop_name, weather_data):
        """获取基于DQN的灌溉建议"""
        try:
            # 获取作物信息
            crop_info = self.crop_data[self.crop_data['Crop'] == crop_name].iloc[0]
            
            # 构建当前状态
            current_state = self.dqn_agent.get_state(
                weather_data=weather_data,
                crop_info={
                    'Temperature': crop_info['Temperature'],
                    'Humidity': crop_info['Humidity'],
                    'Rainfall': crop_info['Rainfall']
                }
            )
            
            # 获取DQN推荐动作
            action = self.dqn_agent.get_action(current_state)
            
            # 转换为实际灌溉量（每个动作对应5mm）
            water_amount = action * 5
            
            # 获取灌溉时间建议
            schedule = self._get_irrigation_timing(
                temperature=weather_data['main']['temp'],
                humidity=weather_data['main']['humidity']
            )
            
            return {
                'water_amount': water_amount,
                'schedule': schedule
            }
            
        except Exception as e:
            print(f"生成灌溉建议时出错: {e}")
            return {'water_amount': 0, 'schedule': '暂无法提供建议'}