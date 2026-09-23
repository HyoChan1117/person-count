import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router/index.js'
import '@fontsource-variable/inter'
import 'pretendard/dist/web/variable/pretendardvariable-dynamic-subset.css'
import './style.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
