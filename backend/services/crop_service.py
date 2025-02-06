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
        """根据温度和湿度确定最佳灌溉时间"""
        if temperature > 30:
            return "建议在清晨或傍晚进行灌溉，避免水分蒸发"
        elif humidity < 40:
            return "建议分多次少量灌溉，避免水分快速流失"
        else:
            return "建议在上午进行灌溉，保证作物充分吸收" 