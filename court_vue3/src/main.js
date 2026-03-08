import { createApp } from 'vue'
import App from './App.vue'
import Router from './tools/Router'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate' 




const app = createApp(App)
const pinia = createPinia()
pinia.use(piniaPluginPersistedstate) 

for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component)
}
app.use(pinia) 
app.use(Router)
app.use(ElementPlus)
app.mount('#app')
