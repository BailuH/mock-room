<template>
    <el-container :id="containerId">
        <el-header class="modern-header">
            <div id="header-title" >
                <h2>数字模拟法庭平台</h2>
            </div>
            <el-avatar :size="45" :src="form.avatarUrl" style="margin-left:auto;margin-top: 5px;"></el-avatar>  
            <div style="margin-left: 10px;color: black;font-size: 17px;margin-top:5px;">欢迎您：{{ form.username }}</div>
            <el-button type="danger" style="margin-left:15px;margin-top:5px;margin-right:5px;" @click="logout">退出登录</el-button>
        </el-header>
        <el-container>
        <el-aside width="235px">
            <el-container id="top">
               <div style="margin:auto;margin-left:15px;margin-top:15px;margin-bottom:10px;color:black;font-size:22px;">导航栏</div>
            </el-container>
            <el-menu class="left-menu" :default-active="$route.path" active-text-color="#409EFF" @select="handleMenuSelect" unique-opened >
                <el-menu-item index="/menu-home" class="anim-item-1">首页</el-menu-item>
                <el-menu-item index="/court" class="anim-item-2">模拟法庭</el-menu-item>
                <el-menu-item index="/case-info" class="anim-item-3">案件相关信息</el-menu-item>
                <el-sub-menu index="4">
                    <template #title>
                        <i class="el-icon-menu"></i>
                        <span style="font-size: 16px;">历史会话</span>
                    </template>
                    <el-menu-item index="/history/plaintiff">原告</el-menu-item>
                    <el-menu-item index="/history/defendant">被告</el-menu-item>
                    <el-menu-item index="/history/judge">审判长</el-menu-item>
                    <el-menu-item index="/history/all-history">全部</el-menu-item>
                </el-sub-menu>
                <el-sub-menu index="5">
                    <template #title>
                        <i class="el-icon-setting"></i>
                        <span style="font-size: 16px;">账户管理</span>
                    </template>
                    <el-menu-item index="/account/personal-info">个人信息</el-menu-item>
                    <el-menu-item index="/account/debate-history">辩论历史</el-menu-item>
                </el-sub-menu>
            </el-menu>
        </el-aside>
        <el-main class="no-border-main">
        <router-view v-slot="{ Component, route }">
    <transition name="content-slide" >
      <div :key="route.fullPath" style="width: 100%; height: 100%;" >
        <component 
          :is="Component" 
        />
      </div>
    </transition>
  </router-view>
        </el-main>
        </el-container>
    </el-container>
</template>

<script >
import  {loginStore}  from '@/tools/Storage';
import { storeToRefs } from 'pinia';
import { computed, ref } from 'vue';
const activeMenu = ref("/menu-home")
const containerId = computed(() => {
    const containerMap = {
    "/court": "container-2"
}
    return containerMap[activeMenu.value]||"container"
})
import { useUserStore} from '@/tools/useUserStore'
import { useRoute } from 'vue-router'
import { useCaseStore } from '@/tools/useCaseStore'; 



export default {
    name: "HomeComponent",
    // 在 Vue 3 选项式 API 中，通常在 setup() 中初始化 store
    setup() {
        const route = useRoute()
        const Store = loginStore();
        const userStore = useUserStore();
        const {form} = storeToRefs(userStore) 
        const caseStore = useCaseStore();
        
        return {form,Store,containerId,route,activeMenu,caseStore};
    },
    data() {
        return {
            // 不要在这里直接赋值，因为 data 只在初始化时执行一次
        };
    },
    methods: {
        logout() {
            // Pinia 不需要 .commit，直接调用方法即可
            this.Store.clearInfo();
            this.$router.push({ name: "login" });
        },
        handleMenuSelect(index) {
            activeMenu.value = index;
            if(index === "/case-info"){
                this.caseStore.fetchCases();
            }
            if(index === "/court"){
        // 强制跳转到绝对路径，并清空所有后缀
                const targetUrl = "http://localhost:5173";
                window.location.href = targetUrl;
                return;
            }
            else{
            this.$router.push({ path: index });}
        }
    }
}




</script>
<style scoped>
/* ========== 1. 全局基础与容器设置 ========== */
:deep(html), :deep(body) {
    margin: 0 !important;
    padding: 0 !important;
    background-color: white !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}

#container {
    display: flex;
    flex-direction: column;
    height: 100vh;
    padding: 0;
    gap: 0;
    background-color: white;
}

#container-2{
     display: flex;
    flex-direction: column;
    height: 100vh;
    padding: 0;
    gap: 0;
    background-color:white;
}

/* ========== 2. Modern Header (玻璃拟态) ========== */
.modern-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 40px;
    height: 70px;
    background: rgba(255, 255, 255, 0.65) !important;
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-bottom: 1px solid rgba(255, 255, 255, 0.3);
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.07);
    position: sticky;
    top: 0;
    z-index: 1000;
    transition: all 0.3s ease;
}

#header-title {
    text-align: center;
    position: absolute;
    left: 50%;
    transform: translateX(-50%);
    font-weight: 600;
    color: #1d1d1f;
}

/* ========== 3. El-Aside (侧边栏卡片化) ========== */
.el-aside {
    border-radius: 12px;
    border-right: none;
    margin: 15px 0 15px 15px; /* 侧边留白让其看起来像悬浮卡片 */
    position: sticky;
    top: 85px; /* Header高度70px + 间隔15px */
    height: calc(100vh - 100px);
    padding: 10px 0;
    overflow-y: auto;
    background-color: #f0f2f5; /* 菜单本身有背景 */
}

.left-menu {
    background-color: #f0f2f5;
    border-right: none;
    font-size: 24px;
}



/* 菜单项样式 */
:deep(.el-menu-item) {
    font-size: 16px;
    margin: 4px 12px;
    border-radius: 10px;
    background-color: #f0f2f5;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

:deep(.el-menu-item.is-active) {
    background-color: white !important;
    color: #409eff;
    font-weight: 600;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

:deep(.el-menu-item:hover) {
    background-color: #f0f7ff !important;
    transform: translateX(4px); /* 悬停微动 */
}

:deep(.el-sub-menu__title:hover) {
    background-color: #f0f7ff !important;
}

/* ========== 4. 主内容区 ========== */
.no-border-main {
    border: none;
    padding: 20px 40px;
    overflow-y: auto;
}

.content-wrapper {
    max-width: 1000px;
    margin: 0 auto;
}


/* ========== 5. 动画效果 (核心部分) ========== */

/* A. 侧边栏菜单项：交错淡入动画 */
@keyframes menuItemSlideIn {
    from {
        opacity: 0;
        transform: translateX(-20px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

/* 为菜单项设置类名或直接作用于 item */
/* 你可以在 el-menu-item 上动态绑定这些 class */
.anim-item-1 { animation: menuItemSlideIn 0.5s ease forwards; animation-delay: 0.1s; opacity: 0; }
.anim-item-2 { animation: menuItemSlideIn 0.5s ease forwards; animation-delay: 0.15s; opacity: 0; }
.anim-item-3 { animation: menuItemSlideIn 0.5s ease forwards; animation-delay: 0.2s; opacity: 0; }
.anim-item-4 { animation: menuItemSlideIn 0.5s ease forwards; animation-delay: 0.25s; opacity: 0; }



/* C. 头部标题切换动画 */
.title-fade-enter-active, .title-fade-leave-active {
    transition: all 0.3s ease;
}

.title-fade-enter-from {
    opacity: 0;
    filter: blur(4px);
    transform: translate(-50%, 5px); /* 保持居中的同时微调位置 */
}

.title-fade-leave-to {
    opacity: 0;
    filter: blur(4px);
    transform: translate(-50%, -5px);
}
</style>

<style>
/* B. 内容区切换动画 (淡入位移) */
.content-slide-enter-active {
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    transition-delay: 0.1s; /* 略微延时，等待旧内容退出 */
}

.content-slide-leave-active {
    transition: all 0.3s cubic-bezier(0.4, 0, 1, 1);
}

.content-slide-enter-from {
    opacity: 0;
    transform: translateY(20px);
}

.content-slide-leave-to {
    opacity: 0;
    transform: translateY(-20px);
}
</style>
