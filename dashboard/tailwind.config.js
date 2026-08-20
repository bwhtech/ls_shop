import frappeUIPreset, { content as frappeUIContent } from "frappe-ui/tailwind"

export default {
	presets: [frappeUIPreset],
	content: [
		"./index.html",
		"./src/**/*.{vue,js,ts,jsx,tsx}",
		// Tailwind v3 does not merge `content` from a preset, so frappe-ui's own source globs
		// have to be listed here or every class it ships is purged.
		...frappeUIContent,
		// frappe-ui's exported list deliberately omits experimental/ListView - it carries no
		// stability promise. Products, Orders and Inventory import ListView from there, so
		// without this glob the list views build clean and render completely unstyled.
		"./node_modules/frappe-ui/experimental/ListView/**/*.{vue,js,ts,jsx,tsx}",
	],
	theme: { extend: {} },
	plugins: [],
}
