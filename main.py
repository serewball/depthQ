from backend.services.weather_service import WeatherService
from backend.services.crop_service import CropService
from datetime import datetime
import os
import pandas as pd
import glob

# 定义几个适合农作物生长的地点
LOCATIONS = {
    '三亚': (18.2528, 109.5127),
    '广州': (23.1291, 113.2644),
    '昆明': (24.8801, 102.8329),
    '海口': (20.0442, 110.1995),
    '南宁': (22.8170, 108.3665)
}

def preprocess_crop_data(crop_service):
    """
    对作物数据进行预处理，每种作物生成一条汇总数据
    """
    # 获取原始数据
    df = crop_service.crop_data
    
    # 按作物名称分组并计算平均值
    processed_data = df.groupby('Crop').agg({
        'Temperature': 'mean',
        'Humidity': 'mean',
        'Rainfall': 'mean'
    }).reset_index()
    
    return processed_data

def generate_crop_status(location_name, lat, lon, weather_service, crop_service, processed_crop_data):
    """为指定地点生成作物状态记录"""
    # 获取天气数据
    print(f"\n获取{location_name}的天气数据...")
    weather_data = weather_service.get_weather_data(lat, lon)
    
    if not weather_data:
        print(f"获取{location_name}天气数据失败")
        return None
    
    # 收集作物状态数据
    crop_status_data = []
    
    # 使用预处理后的数据生成状态记录
    print(f"\n=== 生成{location_name}所有作物的状态记录 ===")
    for _, crop in processed_crop_data.iterrows():
        crop_name = crop['Crop']
        
        # 获取DQN灌溉建议
        irrigation_advice = crop_service.get_irrigation_advice(
            crop_name=crop_name,
            weather_data=weather_data
        )
        
        # 收集作物状态数据
        crop_status_data.append({
            '作物名': crop_name,
            '当前温度(°C)': weather_data['main']['temp'],
            '当前湿度(%)': weather_data['main']['humidity'],
            '当前日降雨量(mm)': weather_data.get('rain', {}).get('1h', 0) * 24,
            '最佳温度(°C)': crop['Temperature'],
            '最佳湿度(%)': crop['Humidity'],
            '最佳日降雨量(mm)': crop['Rainfall'] / 365,
            '灌溉建议(mm)': irrigation_advice['water_amount'],
            '建议时间': irrigation_advice['schedule']
        })
    
    return pd.DataFrame(crop_status_data)

def clean_old_excel_files(output_dir):
    """删除目录中所有的xlsx文件"""
    try:
        # 获取目录中所有的xlsx文件
        excel_files = glob.glob(os.path.join(output_dir, "作物状态记录*.xlsx"))
        
        # 删除每个文件
        for file in excel_files:
            try:
                os.remove(file)
                print(f"已删除旧文件: {file}")
            except Exception as e:
                print(f"删除文件失败 {file}: {e}")
                
    except Exception as e:
        print(f"清理旧文件时出错: {e}")

def save_to_excel(df, location_name, output_dir):
    """保存数据到Excel文件"""
    try:
        # 保存到Excel
        excel_path = os.path.join(output_dir, f"作物状态记录{location_name}.xlsx")
        
        # 设置Excel格式
        writer = pd.ExcelWriter(excel_path, engine='xlsxwriter')
        df.to_excel(writer, index=False, sheet_name='作物状态')
        
        # 设置列宽
        workbook = writer.book
        worksheet = writer.sheets['作物状态']
        worksheet.set_column('A:I', 15)
        
        # 添加条件格式
        red_format = workbook.add_format({'bg_color': '#FFC7CE'})
        
        # 当前温度与最佳温度差异超过±3°C标红
        worksheet.conditional_format('B2:B1000', {
            'type': 'formula',
            'criteria': '=ABS(B2-E2)>3',
            'format': red_format
        })
        
        writer.close()
        print(f"作物状态记录已保存至: {excel_path}")
        return True
        
    except Exception as e:
        print(f"保存{location_name}的Excel文件时出错: {e}")
        return False

def main():
    # 初始化服务
    weather_service = WeatherService()
    crop_service = CropService()
    
    print(f"当前工作目录: {os.getcwd()}")
    
    # 预处理作物数据
    print("\n正在预处理作物数据...")
    processed_crop_data = preprocess_crop_data(crop_service)
    
    # 确保输出目录存在
    output_dir = "D:\\py\\view\\public"
    os.makedirs(output_dir, exist_ok=True)
    
    # 清理旧的Excel文件
    print("\n清理旧的Excel文件...")
    clean_old_excel_files(output_dir)
    
    # 为每个地点生成状态记录
    success_count = 0
    for location_name, (lat, lon) in LOCATIONS.items():
        df = generate_crop_status(location_name, lat, lon, weather_service, crop_service, processed_crop_data)
        if df is not None and save_to_excel(df, location_name, output_dir):
            success_count += 1
    
    print(f"\n智慧灌溉系统运行完成，成功生成 {success_count}/{len(LOCATIONS)} 个地点的状态记录")
    
    # 检查输出文件
    if os.path.exists(output_dir):
        print(f"\n输出目录 {output_dir} 中的文件:")
        for file in os.listdir(output_dir):
            print(f"- {file}")
    else:
        print(f"\n输出目录 {output_dir} 不存在")

if __name__ == "__main__":
    main() 