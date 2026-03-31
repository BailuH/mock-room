<template>
  <el-container :id="containerId" class="layout-container">
    <el-header class="modern-header" :style="{ top: headerVisible ? '0' : '-62px' }" >
      <div id="header-title">
        <img src="@/assets/模谷logo.png" class="logo-container" />
        <h2>模谷</h2>
      </div>
      <el-avatar :size="40" :src="form.avatarUrl" style="margin-left:auto; margin-top: 5px;"></el-avatar>
      <div class="user-welcome">欢迎您：{{ form.username }}</div>
      <el-button type="danger" class="logout-btn" @click="logout">退出登录</el-button>
      <div class="collapse-btn" @click="headerVisible = false">
      <el-icon><ArrowUp /></el-icon>
    </div>
    </el-header>
    <div class="header-show-trigger" @click="headerVisible = true"></div>

    <el-container class="main-body" :style="{ marginTop: headerVisible ? '62px' : '0' }">
      <el-aside :width="isCollapse ? '64px' : '235px'" class="custom-aside">
        
        <div class="aside-label" v-show="!isCollapse">导航栏</div>

        <el-menu 
          class="left-menu" 
          :default-active="$route.path" 
          active-text-color="#409EFF" 
          @select="handleMenuSelect" 
          unique-opened 
          :collapse="isCollapse"
          :collapse-transition="false"
        >
          <el-menu-item index="/menu-home" class="anim-item-1">
            <el-icon><HomeFilled /></el-icon>
            <template #title><span>首页</span></template>
          </el-menu-item>
          
          <el-menu-item index="/court" class="anim-item-2">
            <el-icon><ScaleToOriginal /></el-icon>
            <template #title><span>模拟法庭</span></template>
          </el-menu-item>

          <el-menu-item index="/mofa" class="anim-item-2">
            <el-icon><img src="@/assets/mofa_logo.png" style="width:24px;height: 24px;"/></el-icon>
            <template #title><span>模法小宝</span></template>
          </el-menu-item>
          
          <el-menu-item index="/case-info" class="anim-item-3">
            <el-icon><InfoFilled /></el-icon>
            <template #title><span>案件相关信息</span></template>
          </el-menu-item>

          <el-sub-menu index="4">
            <template #title>
              <el-icon><Memo /></el-icon>
              <span>历史会话</span>
            </template>
            <el-menu-item index="/history/plaintiff">
              <el-icon><UserFilled /></el-icon>
              <template #title><span>原告</span></template>
            </el-menu-item>
            <el-menu-item index="/history/defendant">
              <el-icon><User /></el-icon>
              <template #title><span>被告</span></template>
            </el-menu-item>
            <el-menu-item index="/history/judge">
              <el-icon><Stamp /></el-icon>
              <template #title><span>审判长</span></template>
            </el-menu-item>
          </el-sub-menu>

          <el-sub-menu index="5">
            <template #title>
              <el-icon><Avatar /></el-icon>
              <span>账户管理</span>
            </template>
            <el-menu-item index="/account/personal-info">
              <el-icon><Edit /></el-icon>
              <template #title><span>个人信息</span></template>
            </el-menu-item>
          </el-sub-menu>
        </el-menu>

        <div class="collapse-btn-container" @click="isCollapse = !isCollapse">
          <el-icon v-if="isCollapse"><Expand /></el-icon>
          <el-icon v-else><Fold /></el-icon>
        </div>
      </el-aside>

      <el-main class="no-border-main">
        <router-view v-slot="{ Component, route }">
          <transition name="content-slide">
            <div :key="route.fullPath" class="router-view-wrapper">
              <component :is="Component" />
            </div>
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed} from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { storeToRefs } from 'pinia';
import { loginStore } from '@/tools/Storage';
import { useUserStore } from '@/tools/useUserStore';
import { useCaseStore } from '@/tools/useCaseStore';
// 导入所有需要的图标
import { 
  HomeFilled, ScaleToOriginal, InfoFilled, Memo, 
  UserFilled, User, Stamp, Avatar, Edit, Expand, Fold 
} from '@element-plus/icons-vue';

// 状态定义
const isCollapse = ref(false);
const headerVisible = ref(true);
const activeMenu = ref("/menu-home");

// Store 实例
const router = useRouter();
const route = useRoute();
const Store = loginStore();
const userStore = useUserStore();
const { form } = storeToRefs(userStore);
const caseStore = useCaseStore();

// 计算容器 ID
const containerId = computed(() => {
  return route.path === "/court" ? "container-2" : "container";
});

// 方法定义
const logout = () => {
  Store.clearInfo();
  router.push({ name: "login" });
};

const handleMenuSelect = (index) => {
  activeMenu.value = index;
  if (index === "/case-info") {
    caseStore.fetchCases();
  }
  if (index === "/court") {
    //const caseId = caseStore.currentCaseId;
    //const params = new URLSearchParams({ id: caseId });
    //window.location.href = `http://localhost:5173?${params.toString()}`;
    window.location.href = "http://localhost:5173";
    return;
    //http://82.157.203.240:5173?${params.toString()}
  }
  if (index === "/mofa") {
    window.location.href = "http://fating.zhuibenzhuyan.com";
    return;
  }
  router.push({ path: index });
};


</script>


<style scoped>
/* ========== 1. 基础布局与背景 ========== */
.layout-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  position: relative;
  background-color: #fcfaf7; /* 类似法律文书的羊皮纸色 */
}

.main-body {
  flex: 1;
  display: flex;
  transition: margin-top 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

/* ========== 2. Modern Header (深色木质感) ========== */
.modern-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  display: flex;
  align-items: center;
  padding: 0 40px;
  height: 70px;
  /* 深胡桃木色，展现法庭威严 */
  background: #3e2723 !important; 
  /* 棕金色底边，模拟实木封边 */
  border-bottom: 2px solid #8d6e63; 
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
  z-index: 1001;
  transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

/* 包含 Logo 和 标题的容器 */
#header-title {
  display: flex;
  align-items: center; /* 确保图片和文字在水平线上垂直居中对齐 */
  gap: 12px;           /* Logo 和文字之间的间距 */
}

/* 针对 Logo 图片的布局调整 */
.logo-container {
  height: 45px;        /* 限制图片高度，防止占据大部分屏幕 */
  width: auto;         /* 保持图片原始比例 */
  display: block;      /* 消除图片底部的微小空隙 */
  object-fit: contain; /* 确保图片在缩放时不被拉伸 */
}

/* 标题文字样式 */
#header-title h2 {
  color: #d7ccc8;      /* 浅米棕色文字 */
  font-weight: 700;
  letter-spacing: 2px;
  margin: 0;           /* 清除默认外边距，防止顶破行高 */
  font-size: 1.6rem;   /* 调整文字大小 */
  line-height: 1;      /* 确保文字不会产生额外的上下间距 */
  white-space: nowrap; /* 强制文字不换行 */
}

.logo-container{
  width: 50px;
  height: 50px;
  margin-right: 5px;
}
.user-welcome {
  margin-left: 15px;
  color: #bcaaa4; /* 柔和的次要文字色 */
  font-size: 15px;
}

.logout-btn {
  margin-left: 20px;
  background-color: #795548 !important;
  border-color: #5d4037 !important;
  color: #fcfaf7 !important;
}


/* Header 内部的收起触发器 */
.collapse-btn {
  margin-left: 20px;
  cursor: pointer;
  color: #bcaaa4;
  font-size: 22px;
  display: flex;
  align-items: center;
  transition: color 0.3s;
}
.collapse-btn:hover {
  color: #ffffff;
}

/* ========== 3. 顶部唤醒触发区域 ========== */
.header-show-trigger {
  position: fixed;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 100px;
  height: 20px;
  background-color: #3e2723;
  color: #d7ccc8;
  display: flex;
  justify-content: center;
  align-items: center;
  border-radius: 0 0 10px 10px;
  cursor: pointer;
  z-index: 1000;
  box-shadow: 0 2px 8px rgba(0,0,0,0.2);
  transition: all 0.3s ease;
}
.header-show-trigger:hover {
  height: 30px;
  background-color: #5d4037;
  color: #ffffff;
}

/* ========== 4. 侧边栏 Aside (深棕风格) ========== */
.custom-aside {
  border-radius: 0 12px 12px 0;
  margin: 15px 0 15px 15px;
  height: calc(100vh - 100px);
  background-color: #4e342e; /* 典雅红木色 */
  display: flex;
  flex-direction: column;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  box-shadow: 4px 0 15px rgba(0, 0, 0, 0.15);
}

.aside-label {
  padding: 20px 24px;
  font-size: 16px;
  font-weight: bold;
  color: #d7ccc8;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  white-space: nowrap;
}

/* 菜单样式重置 */
.left-menu {
  flex: 1;
  background-color: transparent !important;
  border: none !important;
  overflow-y: auto;
  overflow-x: hidden;
}

:deep(.el-menu-item), 
:deep(.el-sub-menu__title) {
  padding-left: 20px !important;
  color: #bcaaa4 !important;
}

:deep(.el-menu-item:hover),
:deep(.el-sub-menu__title:hover) {
  background-color: #5d4037 !important;
  color: #ffffff !important;
}

/* 激活态：变为浅色背景，模拟选中的法律文档 */
:deep(.el-menu-item.is-active) {
  background-color: #fcfaf7 !important;
  color: #3e2723 !important;
  font-weight: 700;
}

:deep(.el-icon) {
  width: 24px !important;
  margin-right: 12px !important;
  font-size: 18px !important;
  text-align: center !important;
  color: inherit;
}

/* ========== 5. 底部折叠切换器 ========== */
.collapse-btn-container {
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  background-color: #3e2723;
  color: #bcaaa4;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}
.collapse-btn-container:hover {
  color: #ffffff;
  background-color: #5d4037;
}

/* ========== 6. 内容区与动画 ========== */
.no-border-main {
  padding: 25px 40px;
  flex: 1;
  overflow-y: auto;
}

.router-view-wrapper {
  width: 100%;
  height: 100%;
}

/* 菜单项滑入动画 */
@keyframes menuItemSlideIn {
  from { opacity: 0; transform: translateX(-20px); }
  to { opacity: 1; transform: translateX(0); }
}
.anim-item-1 { animation: menuItemSlideIn 0.4s ease forwards; animation-delay: 0.1s; opacity: 0; }
.anim-item-2 { animation: menuItemSlideIn 0.4s ease forwards; animation-delay: 0.15s; opacity: 0; }
.anim-item-3 { animation: menuItemSlideIn 0.4s ease forwards; animation-delay: 0.2s; opacity: 0; }

/* 内容切换动画 */
.content-slide-enter-active { transition: all 0.4s ease; }
.content-slide-enter-from { opacity: 0; transform: translateY(20px); }
</style>