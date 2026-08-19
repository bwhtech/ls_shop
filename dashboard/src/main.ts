import { FrappeUI } from "frappe-ui"
import { createApp } from "vue"

import App from "./App.vue"
import "./index.css"
import router from "./router"

const app = createApp(App)

// Both are required and they are not the same thing: the plugin installs the app-level
// injections the data-fetching composables rely on, the provider (in App.vue) mounts the
// imperative dialog/toast portals.
app.use(router)
app.use(FrappeUI)

app.mount("#app")
