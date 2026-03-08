<template>
  <div class="login-wrapper">
    <div class="background-carousel">
      <el-carousel 
        indicator-position="none" 
        arrow="never" 
        :interval="7000" 
        height="100vh"
      >
        <el-carousel-item v-for="item in bannerList" :key="item.id">
          <div 
            class="bg-image" 
            :style="{ backgroundImage: `linear-gradient(rgba(0,0,0,0.3), rgba(0,0,0,0.5)), url(${item.url})` }"
          >
            <div class="bg-content-box">
              <h2 class="hero-title">{{ item.title }}</h2>
              <div class="hero-divider"></div>
              <p class="hero-subtitle">{{ item.subtitle }}</p>
            </div>
          </div>
        </el-carousel-item>
      </el-carousel>
    </div>

    <div class="login-card-container">
      <el-card class="glass-card" shadow="always">
        <div class="form-header">
          <h1 class="main-title">数字法庭演示平台</h1>
          <p class="en-subtitle">DIGITAL COURT PLATFORM</p>
        </div>

        <el-tabs v-model="activeTab" stretch class="large-tabs">
          <el-tab-pane label="账号登录" name="login">
            <el-form :model="loginForm" label-position="top" class="login-form">
              <el-form-item label="用户名">
                <el-input 
                  v-model="loginForm.name" 
                  :prefix-icon="User" 
                  placeholder="请输入手机号"
                  size="large"
                />
              </el-form-item>
              <el-form-item label="密码">
                <el-input 
                  v-model="loginForm.password" 
                  :prefix-icon="Lock" 
                  type="password" 
                  placeholder="请输入密码" 
                  show-password 
                  size="large"
                  @keyup.enter="handleLogin"
                />
              </el-form-item>

              <div class="form-options">
                <el-checkbox v-model="rememberMe" class="large-checkbox">下次直接登录</el-checkbox>
                <el-link type="primary" underline="never" class="forget-link">忘记密码？</el-link>
              </div>

              <el-button 
                class="gradient-btn" 
                type="primary" 
                @click.prevent="handleLogin" 
                :loading="loading"
                :disabled="!loginForm.name || !loginForm.password"
              >
                立即登录
              </el-button>
            </el-form>
          </el-tab-pane>

          <el-tab-pane label="新用户注册" name="register">
            <el-form :model="registerForm" label-position="top" class="login-form">
              <el-form-item label="设置用户名">
                <el-input v-model="registerForm.name" :prefix-icon="User" placeholder="请输入手机号" size="large" />
              </el-form-item>
              <el-form-item label="设置密码">
                <el-input v-model="registerForm.password" :prefix-icon="Lock" type="password" placeholder="请设置密码" size="large" show-password />
              </el-form-item>
              <el-button class="submit-btn register-btn" size="large" @click="handleRegister">
                立即注册
              </el-button>
            </el-form>
          </el-tab-pane>
        </el-tabs>

        <div class="form-footer">
          <p>登录即代表同意 <el-link type="primary" underline="hover">《系统服务协议》</el-link></p>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import axios from 'axios'
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import {loginStore} from '@/tools/Storage'
import { useUserStore} from '@/tools/useUserStore'
import { baseURL } from '@/config'




const userStore = loginStore()
const userInfoStore = useUserStore()
const router = useRouter()
const activeTab = ref('login')
const loading = ref(false)
const rememberMe = ref(false)


const loginForm = reactive({ name: '', password: '' })
const registerForm = reactive({ name: '', password: '' })

//const baseURL = 'http://10914zyur6666.vicp.fun:46398'



const bannerList = ref([
  { id: 1, title: '数字法庭 · 模拟辩论', subtitle: '以数字技术深度还原庭审现场，全方位锻造法律实战辩论逻辑。', url: 'https://images.unsplash.com/photo-1589829545856-d10d557cf95f?q=80&w=1200' },
  { id: 2, title: 'AI辅助 · 全新模式', subtitle: '探索人工智能与法律实践的深度融合，定义未来数字法院的全新协作范式', url: 'https://images.unsplash.com/photo-1450101499163-c8848c66ca85?q=80&w=1200' }
])
const handleLogin = async () => {
  loading.value = true
  
  try {
    // 1. 发送请求
    const res = await axios.post(baseURL + '/api/login', {
      type: 'login',
      phone: loginForm.name,
      password: loginForm.password
    })

    // 2. 调试打印：看看后端返回的对象长什么样
    console.log("后端返回对象:", res.data)

    // 3. 修改判断条件：从判断 res.data 变为判断 res.data.msg
    if (res.status === 200 && (res.data.msg || "").includes('顺利完成')) {
      ElMessage.success({ message: '验证通过，欢迎进入系统', duration: 2000 })
      userStore.userName = loginForm.name
      // 4. 保存信息：优先使用后端返回的 userName
      if (rememberMe.value) {
        userStore.saveInfo({
          // 如果后端传回了更准确的用户名，就用后端的，否则用输入框的
          name: res.data.userName || loginForm.name,
          password: loginForm.password,
          rememberMe: true
        })
      } 
        
      

      await userInfoStore.getUserInfo(loginForm.name) // 获取用户信息
      // 跳转首页
      router.push('/')
    } else {
      // 这里的 else 其实很少进入，因为 401 会直接跳到下面的 catch
      ElMessage.error({ message: res.data.msg || '登录失败', duration: 2000 })
    }
  } catch (err) {
    // 5. 专门处理 401 (账号密码错误) 或其他网络错误
    console.error('登录请求失败:', err)
    
    // 尝试获取后端通过 ResponseEntity 返回的错误信息
    const errorMsg = err.response?.data?.msg || '用户名或密码错误'
    ElMessage.error({ message: errorMsg, duration: 2000 })
    
  } finally {
    loading.value = false
  }
}

const handleRegister = async () => {
  try {
    const res = await axios.post(baseURL + '/api/login', {
      type: 'register',
      phone: registerForm.name,
      password: registerForm.password
    });

    // 只有后端成功返回（200 OK）且业务逻辑顺利时才跳转
    if (res.data && String(res.data.msg).includes('顺利完成')) {
      ElMessage.success('申请已提交，请联系管理员审核');
      activeTab.value = 'login'; // 注册成功切换回登录标签，而不是刷新页面
    } else {
      // 处理后端返回的业务错误（如 status 为 error）
      ElMessage.warning(res.data.msg || '注册失败，请重试');
    }
  } catch (err) {
    // 捕获后端抛出的异常（如 400 Bad Request）
    console.error('注册请求失败:', err);
    
    // 获取 FastAPI 返回的 detail 中的错误信息
    const errorDetail = err.response?.data?.detail;
    const errorMsg = typeof errorDetail === 'object' ? errorDetail.msg : (errorDetail || '服务器繁忙');
    
    ElMessage.error(errorMsg);
  }
}

</script>

<style scoped>
.login-wrapper {
  position: relative;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  font-family: "Helvetica Neue", Helvetica, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "微软雅黑", Arial, sans-serif;
}

/* --- 背景轮播优化 --- */
.background-carousel {
  position: absolute;
  width: 100%;
  height: 100%;
  z-index: 1;
}

.bg-image {
  width: 100%;
  height: 100vh;
  background-size: cover;
  background-position: center;
  display: flex;
  align-items: center;
  padding-left: 8%;
}

.bg-content-box {
  color: #fff;
  max-width: 600px;
}

.hero-title {
  font-size: 3.5rem; /* 更大的标题 */
  font-weight: 800;
  letter-spacing: 4px;
  margin-bottom: 15px;
  text-shadow: 0 5px 15px rgba(0,0,0,0.5);
}

.hero-divider {
  width: 80px;
  height: 6px;
  background: #409eff;
  margin-bottom: 25px;
  border-radius: 3px;
}

.hero-subtitle {
  font-size: 1.4rem;
  line-height: 1.6;
  opacity: 0.95;
  text-shadow: 0 2px 8px rgba(0,0,0,0.5);
  font-weight: 300;
}

/* --- 悬浮卡片美化 --- */
.login-card-container {
  position: absolute;
  top: 50%;
  right: 8%;
  transform: translateY(-50%);
  z-index: 10;
  width: 480px; /* 增加宽度 */
}

.glass-card {
  /* 1. 调整透明度：0.88 这是一个兼顾透明感与文字清晰度的黄金比例 */
  background: rgba(255, 255, 255, 0.48) !important;
  
  /* 2. 调整模糊度：20px 增加毛玻璃质感 */
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  
  /* 3. 边框细节：添加一圈极细的白色半透明边框，能让卡片轮廓更对齐、更精致 */
  border: 1px solid rgba(255, 255, 255, 0.4) !important;
  
  /* 4. 内阴影：增加一点向内的微光，提升层次感 */
  box-shadow: 
    0 25px 50px -12px rgba(0, 0, 0, 0.25),
    inset 0 0 20px rgba(255, 255, 255, 0.5) !important;
    
  border-radius: 24px;
  padding: 40px 30px; /* 增加内边距，让内容更对齐、不拥挤 */
}

.form-header {
  text-align: center;
  margin-bottom: 40px;
}

.main-title {
  font-size: 2rem;
  font-weight: 700;
  color: #1a1a1a;
  letter-spacing: 2px;
  margin-bottom: 8px;
}

.en-subtitle {
  font-size: 0.85rem;
  color: #1a1a1a;
  letter-spacing: 4px;
  font-weight: bold;
}

/* --- 表单控件调整 --- */
.large-tabs :deep(.el-tabs__item) {
  font-size: 1.2rem; /* 增大 Tab 字号 */
  height: 60px;
  font-weight: 600;
}

.login-form :deep(.el-form-item__label) {
  font-size: 1.05rem;
  font-weight: 600;
  color: #444;
  padding-bottom: 8px;
}

.login-form :deep(.el-input__inner) {
  height: 50px;
  font-size: 1.1rem;
}

.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 20px 0 30px;
}

.large-checkbox :deep(.el-checkbox__label) {
  font-size: 1rem;
}

.forget-link {
  font-size: 1rem;
}

/* --- 按钮美化 --- */
.gradient-btn {
  width: 100%;
  height: 55px;
  font-size: 1.25rem;
  font-weight: 600;
  letter-spacing: 2px;
  border-radius: 14px;
  background: linear-gradient(135deg, #409eff 0%, #1e40af 100%);
  border: none;
  transition: all 0.3s ease;
}

.gradient-btn:hover {
  transform: translateY(-3px);
  box-shadow: 0 10px 20px rgba(30, 64, 175, 0.3);
}

.register-btn {
  width: 100%;
  height: 55px;
  border-radius: 14px;
  font-size: 1.1rem;
}

.form-footer {
  margin-top: 35px;
  text-align: center;
  font-size: 0.95rem;
  color: #1a1a1a;
  font-weight: 500;
}

/* --- 响应式 --- */
@media (max-width: 1200px) {
  .hero-title { font-size: 2.8rem; }
  .login-card-container { width: 420px; right: 5%; }
}

@media (max-width: 992px) {
  .bg-content-box { display: none; }
  .login-card-container {
    right: 50%;
    transform: translate(50%, -50%);
  }
}
</style>