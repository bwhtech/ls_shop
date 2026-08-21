import path from "node:path"
import vue from "@vitejs/plugin-vue"
import frappeui from "frappe-ui/vite"
import { defineConfig } from "vite"

export default defineConfig({
	plugins: [
		frappeui({
			frappeProxy: {
				// `port` is the VITE dev-server port, not Frappe's. The plugin proxies to
				// whatever webserver_port common_site_config says (8000 here) and routes by
				// the request's Host, so browse the app at <site>:8080 to hit the right site.
				port: 8080,
				// footer_editor_preview is a Frappe-rendered www page the footer editor loads in an
				// iframe. Anything not matched here falls through to vite's SPA fallback, so leaving it
				// out makes the preview pane render the dashboard inside itself instead of the storefront.
				source: "^/(app|login|api|assets|files|private|footer_editor_preview|navbar_editor_preview)(/|\\?|$)",
			},
			jinjaBootData: true,
			lucideIcons: true,
			buildConfig: {
				indexHtmlPath: "../ls_shop/www/dashboard.html",
				emptyOutDir: true,
				sourcemap: true,
				outDir: "../ls_shop/public/dashboard",
				target: "es2015",
			},
		}),
		vue(),
	],
	resolve: {
		alias: {
			"@": path.resolve(__dirname, "src"),
			"tailwind.config.js": path.resolve(__dirname, "tailwind.config.js"),
		},
	},
	optimizeDeps: {
		// frappe-ui and frappe-ui/editor pre-bundle separately and each inlines its own
		// ProseMirror copy, which breaks the editor. Keep frappe-ui out of pre-bundling.
		exclude: ["frappe-ui", "frappe-ui/experimental"],
		// frappe-ui ships a nested CJS feather-icons; pre-bundle it so its default export
		// gets CJS->ESM interop, otherwise FeatherIcon fails and the app never mounts.
		// frappe-ui is excluded above, so its nested CJS deps never get interop'd. Pre-bundle
		// them explicitly or the app dies on module eval with "does not provide an export
		// named 'default'" (feather-icons -> FeatherIcon, debug -> socket.io-client).
		include: [
			"feather-icons",
			"tippy.js",
			"showdown",
			"engine.io-client",
			"socket.io-client",
			"debug",
		],
	},
	server: {
		allowedHosts: true,
	},
})
