import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'

// Skeleton UI
import '@skeletonlabs/skeleton/themes/theme-cerberus.css'
import '@skeletonlabs/skeleton/styles/skeleton.css'
import './assets/app.css'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

app.mount('#app')