import { createApp } from 'vue'
import { FrappeUI, useColorScheme } from 'frappe-ui'
import { router } from './router'
import './style.css'
import App from './App.vue'

// Restores the saved light/dark preference before the first paint. Settings →
// Appearance writes it; this reads it back.
useColorScheme()

const app = createApp(App)
app.use(router)
app.use(FrappeUI)
app.mount('#app')
