<template>
  <div class="home-wrapper">
    <section class="banner-section">
      <el-carousel :interval="5000" arrow="always" height="500px" indicator-position="outside">
        <el-carousel-item v-for="item in bannerList" :key="item.id">
          <div class="banner-card" :style="{ backgroundImage: `linear-gradient(rgba(0,0,0,0.3), rgba(0,0,0,0.5)), url(${item.imageUrl})` }">
            <div class="banner-text">
              <h1 class="animate__animated animate__fadeInUp">{{ item.title }}</h1>
              <p class="animate__animated animate__fadeInUp animate__delay-1s">{{ item.subtitle }}</p>
              <div class="banner-btns animate__animated animate__fadeInUp animate__delay-2s">
                <el-button type="primary" size="large" round @click="handleGo">开始体验</el-button>
                <el-button size="large" round ghost>查看文档</el-button>
              </div>
            </div>
          </div>
        </el-carousel-item>
      </el-carousel>
    </section>

    <section class="feature-section">
      <div class="section-title">
        <h2>核心功能模块</h2>
        <p>为您提供沉浸式模拟法庭辩论体验</p>
      </div>

      <el-row :gutter="30">
        <el-col :xs="24" :sm="12" :md="8" v-for="(feature, index) in featureList" :key="index">
          <el-card class="feature-item" shadow="hover">
            <div class="icon-box" :style="{ backgroundColor: feature.bgColor }">
              <el-icon :size="30" color="#fff">
                <component :is="feature.icon" />
              </el-icon>
            </div>
            <h3>{{ feature.name }}</h3>
            <p>{{ feature.description }}</p>
            <el-link type="primary" :underline="false" @click="handleFunctionGo(feature)">立即体验 <el-icon><ArrowRight /></el-icon></el-link>
          </el-card>
        </el-col>
      </el-row>
    </section>

    
  <el-card 
    class="weather-full-card" 
    v-loading="loading"
    :body-style="{ padding: '40px' }"
  >
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/qweather-icons@1.6.0/font/qweather-icons.css">
    <template #header>
      <div class="card-header">
        <div class="header-main">
          <el-icon class="loc-icon"><LocationFilled /></el-icon>
          <span class="city">{{ cityName }}</span>
          <el-divider direction="vertical" />
          <span class="date-text">{{ weatherDaily?.daily?.[0]?.fxDate }}</span>
        </div>
        <span class="update-tag" v-if="weatherNow.obsTime">
          数据观测时间: {{ formatTime(weatherNow.obsTime) }}
        </span>
      </div>
    </template>

    <div class="weather-layout" v-if="weatherNow.temp">
      <div class="left-panel">
        <div class="temp-main">
          <span class="now-temp">{{ weatherNow?.temp }}</span>
          <span class="now-unit">°C</span>
        </div>
        <div class="status-box">
          <i :class="['weather-icon-huge', 'qi-' + weatherNow?.icon]"></i>
          <div class="status-desc">{{ weatherNow?.text }}</div>
          <div class="temp-range">
            今日全天：{{ weatherDaily?.daily?.[0]?.tempMin }}° ~ {{ weatherDaily?.daily?.[0]?.tempMax }}°
          </div>
        </div>
      </div>

      <div class="right-panel">
        <el-descriptions :column="3" border direction="vertical">
          <el-descriptions-item label="体感温度">
            <span class="value">{{ weatherNow?.feelsLike }}°C</span>
          </el-descriptions-item>
          <el-descriptions-item label="风向风力">
            <span class="value">{{ weatherNow?.windDir }} {{ weatherNow?.windScale }}级</span>
          </el-descriptions-item>
          <el-descriptions-item label="空气湿度">
            <span class="value">{{ weatherNow?.humidity }}%</span>
          </el-descriptions-item>

          <el-descriptions-item label="紫外线指数">
            <span class="value">{{ weatherDaily?.daily?.[0]?.uvIndex }} ({{ getUvDesc(weatherDaily?.daily?.[0]?.uvIndex) }})</span>
          </el-descriptions-item>
          <el-descriptions-item label="能见度">
            <span class="value">{{ weatherDaily?.daily?.[0]?.vis }} km</span>
          </el-descriptions-item>
          <el-descriptions-item label="降水量">
            <span class="value">{{ weatherDaily?.daily?.[0]?.precip }} mm</span>
          </el-descriptions-item>
          
          <el-descriptions-item label="大气压强">
            <span class="value">{{ weatherDaily?.daily?.[0]?.pressure }} hPa</span>
          </el-descriptions-item>
          <el-descriptions-item label="日出时间">
            <span class="value">🌅 {{ weatherDaily?.daily?.[0]?.sunrise }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="日落时间">
            <span class="value">🌇 {{ weatherDaily?.daily?.[0]?.sunset }}</span>
          </el-descriptions-item>
        </el-descriptions>

        <div class="moon-info">
          <span class="moon-label">今日月相：</span>
          <span class="moon-value">{{ weatherDaily?.daily?.[0]?.moonPhase }}</span>
        </div>
      </div>
      <span><i :class="'qi-' + weatherData?.daily?.[0]?.iconDay"></i></span>
    </div>
    <el-skeleton v-else :rows="8" animated />
    <span style="font-size: 12px;color: #999;text-align: right;margin-top: 20px;">数据来源：和风天气</span>
  </el-card>
  <footer class="home-footer">
      <p>© 2026 数字模拟法庭平台 - 保留所有权利</p>
    </footer>
  </div>
</template>

<script setup>
import { ref,onMounted } from 'vue'
import { 
 
  ArrowRight, 
  
} from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
const router = useRouter()

onMounted(async () => {
  await get_weather()
})

import ocrImage from '@/assets/OCR轮播图.png'
import courtImage from '@/assets/模拟法庭轮播图.png'
import teachImage from '@/assets/辅助教学轮播图.png'

// 轮播图数据
const bannerList = ref([
  {
    id: 1,
    title: '智能 OCR 文字识别',
    subtitle: '秒级处理复杂的纸质文书照片，提取文字证据信息',
    imageUrl: ocrImage
    //https://images.unsplash.com/photo-1568605117036-5fe5e7bab0b7?auto=format&fit=crop&q=80&w=1470
  },
  {
    id: 2,
    title: '沉浸体验模拟法庭辩论',
    subtitle: '沉浸式推演法理逻辑・实景化还原庭审交锋',
    imageUrl: courtImage
    //'https://images.unsplash.com/photo-1450101499163-c8848c66ca85?auto=format&fit=crop&q=80&w=1470'
  },
  {
    id: 3,
    title: '全新辅助教学模式',
    subtitle: '创新学习支撑形式・深化课堂学习体验',
    imageUrl: teachImage
    //'https://images.unsplash.com/photo-1550751827-4bd374c3f58b?auto=format&fit=crop&q=80&w=1470'
  }
])


// 功能列表数据 - 修改为指定的六个主题
const featureList = ref([
  {
    name: '法庭辩论模拟',
    description: '通过模拟真实庭审环境，助力学生或律师进行辩论演练与逻辑复盘。',
    icon: 'ChatDotSquare', // 使用对话图标
    bgColor: '#409EFF',
    path: '/court'
  },
  {
    name: '案件证据管理',
    description: '结构化管理案件证据链条，支持多格式材料分类归档与快速索引。',
    icon: 'Files', // 使用文件图标
    bgColor: '#67C23A',
    path: '/case-info'
  },
  {
    name: 'OCR识别提取',
    description: '集成高精度识别引擎，秒级提取纸质文书、图片证据中的关键文字内容。',
    icon: 'Monitor', // 使用屏幕识别图标
    bgColor: '#E6A23C',
    path: '/case-info'
  },
  {
    name: '法庭庭审场景体验',
    description: '选择不同类型角色，参与案件审理、律师辩论，与人工智能互动问答，掌握实用法律知识。',
    icon: 'VideoCamera', // 使用摄像头图标
    bgColor: '#F56C6C',
    path:'/mofa'
  },
  {
    name: '法律服务预约及管理',
    description: '预约律师或法律机构提供的法律服务，由模法小宝提供律师或法律服务机构的实时可约时间表',
    icon: 'Calendar', // 使用日历图标
    bgColor: '#909399',
    path:'/mofa'
  },
  {
    name: '智能法律咨询',
    description: '模法小宝基于超大数据库，结合真实案例与法条法规答疑解惑，给予详细专业的解决流程和策略建议',
    icon: 'ChatLineRound', // 使用咨询图标
    bgColor: '#00CFBD',
    path:'/mofa'
  }
])

const weatherNow = ref({})   // 存储实时天气
const weatherDaily = ref({}) // 存储3天预报
const cityName = ref('正在定位...')
const loading = ref(true)
const apiKey = 'd316bf62e47a4a90930cd9f9ac429c25'
// 你的专用域名前缀
const baseDomain = 'https://ma4jabk88v.re.qweatherapi.com'

const handleGo = () => {
  // 这里可以写路由跳转逻辑，例如 router.push('/dashboard')
  router.push('/court')
  console.log('跳转至工作台')
}

const handleFunctionGo = (feature) => {
  if (feature?.path) {
    if(feature.path === '/mofa') {
      window.location.href = "http://fating.zhuibenzhuyan.com";
      return;
    }
    if(feature.path === '/court'){
      // 生产构建（Docker）下同域访问 /mock-court/，本地开发仍跳转 vite dev server
      window.location.href = process.env.NODE_ENV === "production" ? "/mock-court/" : "http://localhost:5173";
      return;
    }
    router.push(feature.path)
  } else {
    console.log('该功能暂未开放')
  }
}

// 封装天气请求函数，增加异常处理和代码可读性
// 格式化时间
const formatTime = (timeStr) => {
  if (!timeStr) return ''
  return timeStr.substring(11, 16)
}

// 简单的紫外线评价逻辑
const getUvDesc = (index) => {
  const i = parseInt(index)
  if (i <= 2) return '弱'
  if (i <= 5) return '中等'
  if (i <= 7) return '强'
  return '极强'
}


const get_weather = async () => {
  loading.value = true
  try {
    let locationParam = '101010100' // 默认北京

    // 1. 尝试获取浏览器地理位置（经纬度）
    const coords = await new Promise((resolve) => {
      navigator.geolocation.getCurrentPosition(
        (pos) => resolve(`${pos.coords.longitude.toFixed(2)},${pos.coords.latitude.toFixed(2)}`),
        () => resolve(null), // 失败则返回 null
        { timeout: 5000 }
      )
    })

    // 2. 如果拿到经纬度，去反查城市 ID
    if (coords) {
      // 这里的路径严格遵守你提供的文档：/geo/v2/city/lookup
      const geoUrl = `${baseDomain}/geo/v2/city/lookup`
      const geoRes = await axios.get(geoUrl, {
        params: { location: coords, key: apiKey }
      })

      if (geoRes.data.code === '200' && geoRes.data.location?.length > 0) {
        const cityInfo = geoRes.data.location[0]
        cityName.value = cityInfo.name
        locationParam = cityInfo.id
      }
    } else {
      cityName.value = '北京 (定位未授权)'
    }

    // 3. 获取实时天气和预报
    const [nowRes, dailyRes] = await Promise.all([
      axios.get(`${baseDomain}/v7/weather/now`, { params: { location: locationParam, key: apiKey } }),
      axios.get(`${baseDomain}/v7/weather/3d`, { params: { location: locationParam, key: apiKey } })
    ])

    if (nowRes.data.code === '200') weatherNow.value = nowRes.data.now
    if (dailyRes.data.code === '200') weatherDaily.value = dailyRes.data

  } catch (error) {
    console.error('天气获取失败:', error)
    cityName.value = '获取失败'
  } finally {
    loading.value = false
  }
}

</script>

<style scoped>
/* 容器整体样式 */
.home-wrapper {
  background-color: #fcfaf7; 
  min-height: 100vh;
}

/* 轮播区样式 */
.banner-section {
  width: 100%;
}
.banner-card {
  height: 100%;
  background-size: cover;
  background-position: center;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: #fff;
}
.banner-text h1 {
  font-size: 3.5rem;
  margin-bottom: 20px;
  letter-spacing: 2px;
  text-shadow: 0 4px 10px rgba(0,0,0,0.3);
}
.banner-text p {
  font-size: 1.25rem;
  margin-bottom: 30px;
  opacity: 0.9;
}
.banner-btns {
  display: flex;
  gap: 15px;
  justify-content: center;
}

/* 功能区标题 */
.feature-section {
  max-width: 1200px;
  margin: 0 auto;
  padding: 80px 20px;
}
.section-title {
  text-align: center;
  margin-bottom: 60px;
}
.section-title h2 {
  font-size: 2rem;
  color: #303133;
  margin-bottom: 15px;
}
.section-title p {
  color: #909399;
  font-size: 1.1rem;
}

/* 功能卡片样式 */
.feature-item {
  height: 280px;
  margin-bottom: 30px;
  text-align: center;
  transition: all 0.3s;
  border: none;
  border-radius: 12px;
}
.feature-item:hover {
  transform: translateY(-10px);
}
.icon-box {
  width: 70px;
  height: 70px;
  margin: 0 auto 20px;
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 10px 20px rgba(0,0,0,0.1);
}
.feature-item h3 {
  margin-bottom: 12px;
  color: #303133;
}
.feature-item p {
  color: #606266;
  font-size: 0.95rem;
  line-height: 1.6;
  margin-bottom: 15px;
}

/* 底部 */
.home-footer {
  text-align: center;
  padding: 40px 0;
  color: #909399;
  border-top: 1px solid #ebeef5;
}

/* 简单的响应式适配 */
@media (max-width: 768px) {
  .banner-text h1 { font-size: 2rem; }
  .banner-text p { font-size: 1rem; }
}

/* 整体卡片：调宽到 800px 以上，更具呼吸感 */
.weather-full-card {
  max-width: 1300px;
  margin: 0px 0px;
  border-radius: 20px;
  background: #fff;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.08) !important;
  border: none;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-main {
  display: flex;
  align-items: center;
  font-size: 20px;
  font-weight: bold;
}

.loc-icon {
  color: #409eff;
  margin-right: 8px;
}

.date-text {
  color: #606266;
  font-weight: 400;
}

.update-tag {
  font-size: 13px;
  color: #909399;
  background: #f4f4f5;
  padding: 4px 12px;
  border-radius: 20px;
}

/* 左右布局 */
.weather-layout {
  display: flex;
  gap: 40px;
}

.left-panel {
  flex: 0 0 280px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  border-right: 1px solid #f0f0f0;
  padding-right: 20px;
}

.temp-main {
  line-height: 1;
  margin-bottom: 20px;
}

.now-temp {
  font-size: 100px;
  font-weight: 900;
  color: #303133;
}

.now-unit {
  font-size: 30px;
  font-weight: 400;
  margin-left: 5px;
  vertical-align: super;
}

.weather-icon-huge {
  font-size: 80px;
  color: #ff9900;
  display: block;
  margin: 0 auto 10px;
}

.status-desc {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 10px;
}

.temp-range {
  font-size: 15px;
  color: #909399;
}

.right-panel {
  flex: 1;
}

/* 修改 Descriptions 样式使其更好看 */
:deep(.el-descriptions__label) {
  background-color: #fcfdfe !important;
  color: #909399 !important;
  font-weight: 500;
}

.value {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
}

.moon-info {
  margin-top: 25px;
  padding: 15px;
  background: #fdf6ec;
  border-radius: 12px;
  display: inline-block;
  font-size: 14px;
}

.moon-label {
  color: #e6a23c;
}

.moon-value {
  font-weight: bold;
  color: #303133;
}

</style>