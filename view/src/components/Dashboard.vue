<template>
    <div class="container">
      <!-- 页面标题 -->
      <el-container>
        <el-header>
        <div class="header-content">
          <h2>智慧灌溉系统</h2>
          <div class="user-info">
            <span>欢迎, {{ username }}</span>
            <el-button type="text" @click="handleLogout">退出登录</el-button>
          </div>
        </div>
      </el-header>
      <el-main>
        <div class="content-layout">
          <!-- 左侧导航栏 -->
          <el-scrollbar class="crop-menu" hide-scrollbar>
            <el-menu
              class="crop-menu"
              :default-active="currentCrop"
              @select="handleCropSelect">
              <el-menu-item 
                v-for="crop in crops" 
                :key="crop" 
                :index="crop">
                {{ crop }}
              </el-menu-item>
            </el-menu>
          </el-scrollbar>
          <!-- 右侧内容区域 -->
          <div class="chart-container">
            <!-- 地点选择 -->
            <!-- 天气信息卡片 -->
            <el-card class="weather-card">
              <div class="weather-info">
                <div class="weather-item">
                  <el-icon><Sunny /></el-icon>
                  <span>温度: {{ weather.temp }}°C</span>
                </div>
                <div class="weather-item">
                  <el-icon><Cloudy /></el-icon>
                  <span>湿度: {{ weather.humidity }}%</span>
                </div>
                <div class="weather-item">
                  <el-icon><WindPower /></el-icon>
                  <span>风速: {{ weather.windSpeed }} m/s</span>
                </div>
                <div class="weather-item">
                  <el-icon><Umbrella /></el-icon>
                  <span>降水量: {{ weather.rain }} mm</span>
                </div>
                
              </div>
            </el-card>
            <div class="location-selector">
              <el-radio-group v-model="currentLocation" @change="handleLocationChange">
                <el-radio-button v-for="location in locations" 
                               :key="location" 
                               :label="location">
                  {{ location }}
                </el-radio-button>
              </el-radio-group>
            </div>
            <!-- 图表标题 -->
            <div class="chart-title">
              <span style="margin-right: 10px;">地点：{{ currentLocation }}</span>
              <span style="margin-left: 10px;">时间：{{ currentDate }}</span>
              <span style="margin-left: 10px;">建议灌溉时间：{{ suggestTime }}</span>
            </div>
            <div id="main-chart"></div>
          </div>
        </div>
      </el-main>

    </el-container>
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted, computed } from 'vue';
  import * as echarts from 'echarts';
  import * as XLSX from 'xlsx';
  import { useRouter } from 'vue-router';
  import { ElMessage } from 'element-plus';
  import { logout, getWeather } from '../api';
  import { Sunny, Cloudy, WindPower, Umbrella } from '@element-plus/icons-vue';
  
  const router = useRouter();
  
  // 作物列表
  const crops = [
    "Apple", "Banana", "Blackgram", "ChickPea", "Coconut",
    "Coffee", "Cotton", "Grapes", "Jute", "KidneyBeans",
    "Lentil", "Maize", "Mango", "MothBeans", "MungBean",
    "Muskmelon", "Orange", "Papaya", "PigeonPeas", "Pomegranate",
    "Rice", "Watermelon"
  ];
  
  const currentCrop = ref('Apple');
  const cropData = ref(null);
  let myChart = null;
  const suggestTime = ref('');
  // 当前时间
  const currentDate = computed(() => {
    const now = new Date();
    return now.toLocaleDateString(); // 格式化为本地日期字符串
  });
  
  // 地点列表
  const locations = ['三亚', '广州', '昆明', '海口', '南宁'];
  const currentLocation = ref('广州');
  
  // 加载Excel数据
  const loadExcelData = async (location) => {
    try {
      const response = await fetch(`./作物状态记录${location}.xlsx`);
      const arrayBuffer = await response.arrayBuffer();
      const data = new Uint8Array(arrayBuffer);
      const workbook = XLSX.read(data, { type: 'array' });
      const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
      cropData.value = XLSX.utils.sheet_to_json(firstSheet);
    } catch (error) {
      console.error('加载Excel数据失败:', error);
      ElMessage.error('加载数据失败');
    }
  };
  
  // 初始化图表
  const initChart = () => {
    const chartDom = document.getElementById('main-chart');
    myChart = echarts.init(chartDom);
  };
  
  // 更新图表数据
  const updateChart = (cropName) => {
    if (!cropData.value || !myChart) return;
  
    const cropInfo = cropData.value.find(item => item['作物名'] === cropName);
    if (!cropInfo) return;
    suggestTime.value = cropInfo['建议时间'];
    console.log('灌溉量数据:', { 
      原始值: cropInfo,
      转换后: parseFloat(cropInfo['建议灌溉量'] || 0).toFixed(2)
    });
  
    const option = {
      title: {
        text: `${cropName}生长环境对比`,
        left: 'center'
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow'
        }
      },
      legend: {
        data: ['当前条件', '最佳条件', '建议灌溉量'], 
        top: 25
      },
      xAxis: {
        type: 'category',
        data: ['温度(°C)', '湿度(%)', '日降水量(mm)', '建议灌溉量(mm)'] 
      },
      yAxis: [{
        type: 'value',
        name: '环境指标'
      },
      {
        type: 'value',
        name: '灌溉量',
        position: 'right'
      }],
      series: [
        {
          name: '当前条件',
          type: 'bar',
          data: [
            parseFloat(cropInfo['当前温度(°C)']).toFixed(2),
            parseFloat(cropInfo['当前湿度(%)']).toFixed(2),
            parseFloat(cropInfo['当前日降雨量(mm)']).toFixed(2),
            null
          ],
          itemStyle: {
            color: '#91CC75'
          },
          label: {
                  show: true,
                  position: 'top'
              },
        },
        {
          name: '最佳条件',
          type: 'bar',
          data: [
            parseFloat(cropInfo['最佳温度(°C)']).toFixed(2),
            parseFloat(cropInfo['最佳湿度(%)']).toFixed(2),
            parseFloat(cropInfo['最佳日降雨量(mm)']).toFixed(2),
            null
          ],
          itemStyle: {
            color: '#5470C6'
          },
          label: {
                  show: true,
                  position: 'top'
              },
        },
        {
          name: '建议灌溉量',
          type: 'bar',
          yAxisIndex: 1,
          data: [
            null,
            null,
            null,
            parseFloat(cropInfo['灌溉建议(mm)'] || 0).toFixed(2)
          ],
          itemStyle: {
            color: '#FAC858'
          },
          label: {
            show: true,
            position: 'top',
            formatter: '{c}',
            color: '#000000',
            fontSize: 12,
            fontWeight: 'bold'
          }
        }
      ]
    };
  
    myChart.setOption(option);
  };
  
  // 处理作物选择
  const handleCropSelect = (cropName) => {
    currentCrop.value = cropName;
    updateChart(cropName);
  };
  
  // 天气数据
  const weather = ref({
    temp: '--',
    humidity: '--',
    windSpeed: '--',
    rain: '--'
  });
  
  // 获取天气信息
  const fetchWeather = async (location) => {
    try {
      const res = await getWeather(location);
      if (res.code === 200) {
        weather.value = res.data;
      }
    } catch (error) {
      console.error('获取天气信息失败:', error);
      ElMessage.error('获取天气信息失败');
    }
  };
  
  // 处理地点切换
  const handleLocationChange = async (location) => {
    currentLocation.value = location;
    await loadExcelData(location);
    await fetchWeather(location);
    updateChart(currentCrop.value);
  };
  
  // 组件挂载时初始化
  onMounted(async () => {
    await loadExcelData(currentLocation.value);
    await fetchWeather(currentLocation.value);
    initChart();
    updateChart(currentCrop.value);
    
    // 添加窗口大小变化监听
    window.addEventListener('resize', () => {
      myChart?.resize();
    });
  });
  
  const username = ref(localStorage.getItem('username') || '用户');
  
  const handleLogout = async () => {
    try {
      const res = await logout();
      if (res.code === 200) {
        // 清除本地存储的认证信息
        localStorage.removeItem('token');
        localStorage.removeItem('username');
        
        ElMessage.success('退出成功');
        // 跳转到登录页
        router.push('/login');
      }
    } catch (error) {
      ElMessage.error(error.message || '退出失败');
    }
  };
  </script>
  
  <style scoped>
  .container {
    height: 100vh;
    width: 100%;
  }
  
  .content-layout {
    display: flex;
    height: 100%;
  }
  
  .crop-menu {
    width: 200px;
    height: 100%;
    border-right: 1px solid #e6e6e6;
  }
  
  .chart-container {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 20px;
  }
  
  .chart-title {
    text-align: center;
    font-size: 16px;
    color: #666;
    margin-bottom: 20px;
  }
  
  #main-chart {
    width: 800px;
    height: 400px;
  }
  
  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    height: 100%;
  }
  
  .user-info {
    display: flex;
    align-items: center;
    gap: 15px;
  }
  
  .el-header {
    background-color: #fff;
    border-bottom: 1px solid #dcdfe6;
    padding: 0 20px;
  }
  
  h2 {
    margin: 0;
    color: #333;
  }
  
  .el-main {
    padding: 0;
    height: calc(100vh - 60px);
  }
  
  .weather-card {
    width: 100%;
    margin-bottom: 20px;
  }
  
  .weather-info {
    display: flex;
    justify-content: space-around;
    align-items: center;
    padding: 10px;
  }
  
  .weather-item {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 16px;
  }
  
  .weather-item .el-icon {
    font-size: 24px;
    color: #409EFF;
  }
  
  .location-selector {
    margin-bottom: 20px;
    text-align: center;
  }
  
  .el-radio-group {
    margin-bottom: 15px;
  }
  
  .el-radio-button {
    margin: 0 5px;
  }
  </style>