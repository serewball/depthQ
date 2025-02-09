<template>
  <div class="container">
    <!-- 页面标题 -->
    <div class="page-title">智慧灌溉系统</div>
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
    <!-- 右侧图表 -->
    <div class="chart-container">
      <!-- 图表标题 -->
      <div class="chart-title">
         <span style="margin-right: 10px;"> 地点：广州 </span>
        时间：{{ currentDate }}
      </div>
      <div id="main-chart" style="width: 800px; height: 400px;"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import * as echarts from 'echarts';
import * as XLSX from 'xlsx';

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

// 当前时间
const currentDate = computed(() => {
  const now = new Date();
  return now.toLocaleDateString(); // 格式化为本地日期字符串
});

// 加载Excel数据
const loadExcelData = async () => {
  try {
    const response = await fetch('./作物状态记录广州.xlsx');
    const arrayBuffer = await response.arrayBuffer();
    const data = new Uint8Array(arrayBuffer);
    const workbook = XLSX.read(data, { type: 'array' });
    const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
    cropData.value = XLSX.utils.sheet_to_json(firstSheet);
  } catch (error) {
    console.error('加载Excel数据失败:', error);
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
          parseFloat(cropInfo['当前温度']).toFixed(2),
          parseFloat(cropInfo['当前湿度']).toFixed(2),
          parseFloat(cropInfo['当前日降雨量']).toFixed(2),
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
          parseFloat(cropInfo['最佳温度']).toFixed(2),
          parseFloat(cropInfo['最佳湿度']).toFixed(2),
          parseFloat(cropInfo['最佳日降雨量']).toFixed(2),
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
          parseFloat(cropInfo['建议灌溉量'] || 0).toFixed(2)
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

// 组件挂载时初始化
onMounted(async () => {
  await loadExcelData();
  initChart();
  updateChart(currentCrop.value);
  
  // 添加窗口大小变化监听
  window.addEventListener('resize', () => {
    myChart?.resize();
  });
});
</script>

<style scoped>
.container {
  display: flex;
  height: 100vh;
}

.page-title {
  position: absolute;
  top: 10px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 24px;
  font-weight: bold;
  color: #333;
}

.chart-title {
  text-align: center;
  font-size: 16px;
  color: #666;
  margin-bottom: 30px;
}

.crop-menu {
  width: 200px;
  height: 100%;
  overflow-y: auto;
  border-right: 1px solid #e6e6e6;
}

.chart-container {
  flex: 1;
  padding: 20px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}
</style>