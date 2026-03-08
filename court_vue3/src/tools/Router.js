import {createRouter,createWebHashHistory} from 'vue-router';
import LoginComponent from '../components/login/LoginComponent.vue';
import HomeComponent from '../components/home/HomeComponent.vue';
import AllHistoryComponent from '@/components/menu/AllHistoryComponent.vue';
import CaseInfoComponent from '@/components/menu/CaseInfoComponent.vue';
import CourtComponent from '@/components/menu/CourtComponent.vue';
import DebateHistoryComponent from '@/components/menu/DebateHistoryComponent.vue';
import DefendantComponent from '@/components/menu/DefendantComponent.vue';
import JudgeComponent from '@/components/menu/JudgeComponent.vue';
import PersonalInfo from '@/components/menu/PersonalInfo.vue';
import PlaintiffComponent from '@/components/menu/PlaintiffComponent.vue';
import MenuHome from '@/components/menu/MenuHome.vue';
import { loginStore} from '@/tools/Storage'

const Router = createRouter({
    history:createWebHashHistory(),
    routes:[
        {
            path:'/',
            component:HomeComponent,
            meta:{title:'数字法庭 · 首页'},
            redirect:'/menu-home',
            children:[
                {
            path: 'history/all-history',
            component:AllHistoryComponent,
            name:'all-history'
        },
        {
            path: 'case-info',
            component:CaseInfoComponent,
            meta:{title:'数字法庭 · 案件管理'},
            name:'case-info'
        },
        {
            path: 'court',
            component:CourtComponent,
            meta:{title:'数字法庭 · 模拟法庭'},
            name:'court'
        },
        {
            path: 'account/debate-history',
            component:DebateHistoryComponent,
            meta:{title:'数字法庭 · 辩论历史'},
            name:'debate-history'
        },
        {
            path: 'history/defendant',
            component:DefendantComponent,
            meta:{title:'数字法庭 · 被告信息'},
            name:'defendant'
        },
        {
            component:JudgeComponent,
            meta:{title:'数字法庭 · 法官信息'},
            path: 'history/judge',
            name:'judge'
        },
        {
            path: 'account/personal-info',
            component:PersonalInfo,
            meta:{title:'数字法庭 · 个人信息'},
            name:'personal-info'
        },
        {
            path: 'history/plaintiff',
            component:PlaintiffComponent,
            name:'plaintiff',
            meta:{title:'数字法庭 · 辩论历史'},
        },
        {
            path:'menu-home',
            component:MenuHome,
            name:'menu-home'
        }
            ]
        },
        {
            path:'/login',
            component:LoginComponent,
            name:'login'
        }
        
        
    ]
})

// 注意参数顺序：to 是目的地，from 是来源
Router.beforeEach((to) => {
    // 1. 设置标题
    document.title = to.meta.title || '数字法庭';

    const Store = loginStore();

    // 2. 如果要去的是登录页，直接放行，否则会死循环
    if (to.name === 'login') {
        return true;
    }

    // 3. 检查是否登录（比如判断用户名是否为空）
    if (Store.userName === "") {
        // 未登录，无论你想去哪，都强制跳转到登录页
        return { name: 'login' };
    }

    // 4. 已登录，允许访问所有页面
    return true;
});

export default Router;