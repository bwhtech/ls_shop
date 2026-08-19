import { createApp } from "vue"

import {
	Badge,
	Button,
	Dialog,
	ErrorMessage,
	FormControl,
	frappeRequest,
	pageMetaPlugin,
	resourcesPlugin,
	setConfig,
} from "frappe-ui"

import App from "./App.vue"
import "./index.css"
import router from "./router"

const globalComponents = { Button, FormControl, ErrorMessage, Dialog, Badge }

const app = createApp(App)

setConfig("resourceFetcher", frappeRequest)

app.use(router)
app.use(resourcesPlugin)
app.use(pageMetaPlugin)

for (const [key, component] of Object.entries(globalComponents)) {
	app.component(key, component)
}

app.mount("#app")
