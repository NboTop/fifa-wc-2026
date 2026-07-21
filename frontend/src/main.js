import axios from 'axios'
axios.defaults.baseURL = import.meta.env.VITE_API_BASE_URL || ''
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
createApp(App).use(router).mount('#app')
