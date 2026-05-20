import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

import App from './App.vue'
import router from './router'
import './styles/variables.scss'

const app = createApp(App)

// 应用保存的主题
const savedTheme = localStorage.getItem('theme')
if (savedTheme === 'dark') {
  document.documentElement.classList.add('dark')
}

app.use(createPinia())
app.use(router)
app.use(ElementPlus)

app.mount('#app')