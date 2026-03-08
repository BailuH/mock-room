import { defineStore } from 'pinia';
import axios from 'axios';
import { baseURL } from '@/config'

//const baseURL = 'http://10914zyur6666.vicp.fun:46398'




export const useUserStore = defineStore('user', {
  /**
   * state: 存储最终确认的个人信息
   * 注意：组件内部会使用一套 localForm 副本，只有点击“保存”时才会同步到这里
   */
  state: () => ({
    // 基础资料
    form: {
      username: "",
      uid: "880124",
      email: "zhangsan@example.com",
      phone: "",
      // 默认头像地址
      avatarUrl: "https://api.dicebear.com/7.x/avataaars/svg?seed=Alex",
    },
    // 安全设置相关（通常由后端返回，不可直接修改）
    security: {
      level: 75,
      lastLogin: "2024-05-20 14:30",
      isTwoFactorEnabled: false
    }
  }),

  getters: {
    /**
     * 根据安全分数返回状态文字
     */
    securityStatusText: (state) => {
      if (state.security.level > 80) return '高';
      if (state.security.level > 50) return '一般';
      return '较低';
    }
  },

  actions: {
    // 假设这是在 Vue 或 React 组件的方法中
async getUserInfo(phone) {
    try {
        
        
        // 1. 判空检查（可选，但推荐）
        if (!phone) {
            console.error("未找到用户信息");
            return;
        }

        // 2. URL 拼接修正：
        // 后端是 /basicInfo/{phone}，所以不能用 ?phone=
        // 假设 baseURL 是域名 (如 http://localhost:8000)
        const response = await axios.get(`${baseURL}/api/basicInfo/${phone}`);

        // 3. 获取数据
        // axios 的返回结果包裹在 .data 中
        const userData = response.data;
        
        console.log("获取成功:", userData);
        
        this.form.username = userData.username;
        this.form.email = userData.email;
        this.form.phone = userData.phone;
        this.form.avatarUrl = userData.avatarUrl;

        return userData;

    } catch (error) {
        // 4. 错误处理
        if (error.response && error.response.status === 404) {
             console.error("用户不存在");
        } else {
             console.error("请求发生错误:", error);
        }
    }
},
    /**
     * 保存全局个人信息
     * @param {Object} updatedData 来自组件 localForm 的副本
     */
    async saveGlobalInfo(updatedData) {
    try {
      // 1. 准备数据：先把新数据和旧数据合并，计算出最终要保存的样子
      // 注意：这里先用一个临时变量，不要直接改 this.form，万一请求失败了好回滚
      const finalData = { ...this.form, ...updatedData };

      // 2. 发送请求
      // 注意：这里必须手动把前端的【驼峰】转成后端要的【下划线】
      await axios.post(`${baseURL}/api/basicInfo/update/${finalData.phone}`, {
        user_name: finalData.username || "",   // 前端 username -> 后端 user_name
        email: finalData.email || "",          // email 一样
        avatar_url: finalData.avatarUrl || ""  // 前端 avatarUrl -> 后端 avatar_url
      });

      // 3. 请求成功后，再正式更新 Pinia 的 State
      this.form = finalData;
      
      console.log("Store: 个人信息已同步更新");

    } catch (error) {
      console.error("Store: 保存失败", error);
      // 继续抛出错误，这样前端组件里的 try-catch 也能捕获到，从而弹出“保存失败”的提示
      throw error;
    }
  },
    /**
     * 仅更新头像（如果裁剪完立即上传服务器，可以用这个）
     */
    updateAvatar(newUrl) {
      this.form.avatarUrl = newUrl;
    },

    /**
     * 重置用户信息（如退出登录时调用）
     */
    resetUserInfo() {
      this.$reset();
    }
  },

  // 开启持久化配置
  persist: {
    key: 'court-user-storage', // 存储在 localStorage 中的 key
    storage: localStorage,      // 存储方式
    paths: ['form', 'security'] // 指定需要持久化的字段
  }
});