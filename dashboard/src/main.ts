import { FrappeUI } from "frappe-ui"
import { createApp } from "vue"

import App from "./App.vue"
import { applyDocumentDirection } from "./composables/useLocale"
import "./index.css"
import router from "./router"

// Ahead of mount: a shell that painted LTR first would visibly snap around on an Arabic session.
applyDocumentDirection()

const app = createApp(App)

// Both are required: the plugin installs the app-level injections the data-fetching composables rely on,
// the provider (in App.vue) mounts the imperative dialog/toast portals.
app.use(router)
app.use(FrappeUI)

app.mount("#app")
