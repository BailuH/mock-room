import { defineStore} from 'pinia';


export const loginStore = defineStore('loginStore',{
    state:() => {
        
        return {
            userName:"",
            userPassword:"",
            rememberMe:false,
           
        }
    },
    actions: {
        saveInfo(userInfo = {}) { 
        // 使用解构获取值，并提供逻辑短路保护
        const { name, password, rememberMe } = userInfo;
        
        this.userName = name || "";
        this.userPassword = password || "";
        this.rememberMe = !!rememberMe; // 确保转为布尔值
    },
        clearInfo(){
            this.userName = "";
            this.userPassword = "";
            this.rememberMe = false;
        }
    },
    persist: {
    key: 'login-info', // 存储在 localStorage 中的 key
    storage: localStorage,      // 存储方式
    paths: ['userName', 'userPassword','rememberMe'] // 指定需要持久化的字段
  }

})







