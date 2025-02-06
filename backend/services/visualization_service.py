import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
import os
from matplotlib import font_manager

class VisualizationService:
    def __init__(self):
        self.irrigation_history = []
        # 创建基础输出目录
        self.base_output_dir = os.path.join(os.getcwd(), 'output')
        self.images_dir = os.path.join(self.base_output_dir, 'images')
        try:
            os.makedirs(self.base_output_dir, exist_ok=True)
            os.makedirs(self.images_dir, exist_ok=True)
            print(f"基础目录创建成功: {self.base_output_dir}")
        except Exception as e:
            print(f"创建基础目录失败: {e}")
            
        # 设置中文字体
        try:
            # 对于Windows系统
            if os.name == 'nt':
                plt.rcParams['font.family'] = ['Microsoft YaHei']
            # 对于Linux/Mac系统
            else:
                plt.rcParams['font.family'] = ['Arial Unicode MS']
            
            plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
            print("中文字体设置成功")
        except Exception as e:
            print(f"设置中文字体失败: {e}")
        
    def add_irrigation_record(self, timestamp, crop_name, water_amount, conditions):
        """添加灌溉记录"""
        try:
            self.irrigation_history.append({
                'timestamp': timestamp,
                'crop_name': crop_name,
                'water_amount': water_amount,
                'temperature': conditions['temperature'],
                'humidity': conditions['humidity'],
                'rainfall': conditions['daily_rainfall']
            })
            print(f"成功添加灌溉记录: {crop_name}")
        except Exception as e:
            print(f"添加灌溉记录失败: {e}")
    
    def get_next_number(self, crop_name):
        """获取下一个可用的序号"""
        # 创建作物目录
        crop_dir = os.path.join(self.images_dir, crop_name)
        if not os.path.exists(crop_dir):
            os.makedirs(crop_dir)
            print(f"创建作物目录: {crop_dir}")
        
        # 获取当前所有图片的编号
        existing_nums = []
        for f in os.listdir(crop_dir):
            try:
                # 从文件名中提取序号（如 "001_作物状态.png"）
                num = int(f.split('_')[0])
                existing_nums.append(num)
            except (ValueError, IndexError):
                continue
        
        # 确定下一个序号
        next_num = 1 if not existing_nums else max(existing_nums) + 1
        return crop_dir, next_num
    
    def plot_current_status(self, crop_info, current_conditions, optimal_conditions):
        """绘制当前作物状态对比图"""
        try:
            # 获取作物目录和下一个序号
            crop_dir, next_num = self.get_next_number(crop_info['name'])
            
            plt.figure(figsize=(12, 6))
            
            # 设置条形图的位置
            x = range(3)
            width = 0.35
            
            # 当前条件
            current_values = [
                current_conditions['temperature'],
                current_conditions['humidity'],
                current_conditions['daily_rainfall']
            ]
            
            # 最佳条件
            optimal_values = [
                optimal_conditions['temperature'],
                optimal_conditions['humidity'],
                optimal_conditions['daily_rainfall']
            ]
            
            # 绘制条形图
            plt.bar(x, current_values, width, label='当前条件', color='skyblue')
            plt.bar([i + width for i in x], optimal_values, width, label='最佳条件', color='lightgreen')
            
            # 设置图表标签
            plt.xlabel('环境参数')
            plt.ylabel('数值')
            plt.title(f'{crop_info["name"]}生长环境对比')
            plt.xticks([i + width/2 for i in x], ['温度(°C)', '湿度(%)', '日降水量(mm)'])
            plt.legend()
            
            # 添加数值标签
            for i, v in enumerate(current_values):
                plt.text(i, v, f'{v:.1f}', ha='center', va='bottom')
            for i, v in enumerate(optimal_values):
                plt.text(i + width, v, f'{v:.1f}', ha='center', va='bottom')
            
            # 保存图表，使用序号作为文件名前缀
            save_path = os.path.join(crop_dir, f"{next_num:03d}_作物状态.png")
            if not os.path.exists(save_path):  # 只在文件不存在时保存
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                plt.close()
                print(f"作物状态图已保存至: {save_path}")
            else:
                plt.close()
                print(f"作物状态图已存在: {save_path}")
            
        except Exception as e:
            print(f"生成作物状态图失败: {e}")
    
    def plot_irrigation_history(self, crop_name):
        """绘制灌溉历史记录"""
        try:
            if not self.irrigation_history:
                print("没有灌溉历史记录，跳过绘图")
                return
            
            # 获取作物目录和下一个序号
            crop_dir, next_num = self.get_next_number(crop_name)
            
            df = pd.DataFrame(self.irrigation_history)
            
            plt.figure(figsize=(12, 8))
            
            # 绘制灌溉量变化
            plt.subplot(2, 1, 1)
            plt.plot(df['timestamp'], df['water_amount'], marker='o', label='灌溉量')
            plt.title('灌溉历史记录')
            plt.xlabel('时间')
            plt.ylabel('灌溉量(mm)')
            plt.legend()
            
            # 绘制环境条件变化
            plt.subplot(2, 1, 2)
            plt.plot(df['timestamp'], df['temperature'], marker='s', label='温度(°C)')
            plt.plot(df['timestamp'], df['humidity'], marker='^', label='湿度(%)')
            plt.plot(df['timestamp'], df['rainfall'], marker='v', label='降雨量(mm)')
            plt.xlabel('时间')
            plt.ylabel('数值')
            plt.legend()
            
            plt.tight_layout()
            
            # 保存图表，使用序号作为文件名前缀
            save_path = os.path.join(crop_dir, f"{next_num:03d}_灌溉历史.png")
            if not os.path.exists(save_path):  # 只在文件不存在时保存
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                plt.close()
                print(f"灌溉历史图已保存至: {save_path}")
            else:
                plt.close()
                print(f"灌溉历史图已存在: {save_path}")
            
        except Exception as e:
            print(f"生成灌溉历史图失败: {e}") 