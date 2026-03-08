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
            <el-link type="primary" :underline="false">了解更多 <el-icon><ArrowRight /></el-icon></el-link>
          </el-card>
        </el-col>
      </el-row>
    </section>

    <footer class="home-footer">
      <p>© 2026 数字模拟法庭平台 - 保留所有权利</p>
    </footer>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { 
 
  ArrowRight 
} from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
const router = useRouter()
// 轮播图数据
const bannerList = ref([
  {
    id: 1,
    title: '智能 OCR 文字识别',
    subtitle: '秒级处理复杂的纸质文书照片，提取文字证据信息',
    imageUrl: 'https://images.unsplash.com/photo-1568605117036-5fe5e7bab0b7?auto=format&fit=crop&q=80&w=1470'
  },
  {
    id: 2,
    title: '沉浸体验模拟法庭辩论',
    subtitle: '沉浸式推演法理逻辑・实景化还原庭审交锋',
    imageUrl: 'https://images.unsplash.com/photo-1450101499163-c8848c66ca85?auto=format&fit=crop&q=80&w=1470'
  },
  {
    id: 3,
    title: '全新辅助教学模式',
    subtitle: '创新学习支撑形式・深化课堂学习体验',
    imageUrl: 'https://images.unsplash.com/photo-1550751827-4bd374c3f58b?auto=format&fit=crop&q=80&w=1470'
  }
])

// 功能列表数据
// 功能列表数据 - 修改为指定的六个主题
const featureList = ref([
  {
    name: '法庭辩论模拟',
    description: '通过模拟真实庭审环境，助力学生或律师进行辩论演练与逻辑复盘。',
    icon: 'ChatDotSquare', // 使用对话图标
    bgColor: '#409EFF'
  },
  {
    name: '案件证据管理',
    description: '结构化管理案件证据链条，支持多格式材料分类归档与快速索引。',
    icon: 'Files', // 使用文件图标
    bgColor: '#67C23A'
  },
  {
    name: 'OCR识别提取',
    description: '集成高精度识别引擎，秒级提取纸质文书、图片证据中的关键文字内容。',
    icon: 'Monitor', // 使用屏幕识别图标
    bgColor: '#E6A23C'
  },
  {
    name: '人工智能分析',
    description: '深度分析案情文本，自动识别相关人员、时间线及潜在法律风险点。',
    icon: 'Cpu', // 使用处理芯片图标
    bgColor: '#F56C6C'
  },
  {
    name: '隐私安全保护',
    description: '本地化处理敏感数据，记录随用随清理，确保司法材料的绝对私密性。',
    icon: 'Lock', // 使用锁定图标
    bgColor: '#909399'
  },
  {
    name: '辅助教学模式',
    description: '专为法学教育设计，支持案例拆解、知识点标注及教学进度实时同步。',
    icon: 'Reading', // 使用阅读/教学图标
    bgColor: '#00CFBD'
  }
])

const handleGo = () => {
  // 这里可以写路由跳转逻辑，例如 router.push('/dashboard')
  router.push('/court')
  console.log('跳转至工作台')
}
</script>

<style scoped>
/* 容器整体样式 */
.home-wrapper {
  background-color: #fcfcfc;
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
</style>