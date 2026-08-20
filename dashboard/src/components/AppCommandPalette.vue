<script setup lang="ts">
import { openAddProduct } from "@/components/addProduct"
import { showPalette, showShortcuts } from "@/components/commandPalette"
import { openSettings } from "@/components/settings"
import type { OrderRow, ProductRow } from "@/types"
import { useEventListener } from "@vueuse/core"
import {
	CommandPalette,
	CommandPaletteItem,
	KeyboardShortcutsModal,
	formatShortcutLabel,
	useCall,
	useShortcut,
	useTheme,
} from "frappe-ui"
import { type Component, computed, h, markRaw, ref, watch } from "vue"
import { useRouter } from "vue-router"

type PaletteItem = {
	name: string
	title: string
	description?: string
	icon: Component
	action: () => void
}

const router = useRouter()
const { setTheme, currentTheme } = useTheme()

const searchQuery = ref("")

// CommandPaletteItem renders `item.icon` through `<component :is>`, so a lucide class name has
// to arrive wrapped in a component rather than as the bare string the rest of the app passes.
function lucide(name: string): Component {
	return () => h("span", { class: name, "aria-hidden": "true" })
}

const icons = {
	home: lucide("lucide-house"),
	orders: lucide("lucide-receipt"),
	products: lucide("lucide-package"),
	inventory: lucide("lucide-boxes"),
	navigation: lucide("lucide-menu"),
	footer: lucide("lucide-panel-bottom"),
	profile: lucide("lucide-circle-user"),
	appearance: lucide("lucide-palette"),
	store: lucide("lucide-store"),
	shipping: lucide("lucide-truck"),
	payments: lucide("lucide-credit-card"),
	advanced: lucide("lucide-settings-2"),
	add: lucide("lucide-plus"),
	storefront: lucide("lucide-external-link"),
	light: lucide("lucide-sun"),
	dark: lucide("lucide-moon"),
	system: lucide("lucide-monitor"),
	keyboard: lucide("lucide-keyboard"),
}

function go(route: string) {
	router.push({ name: route })
}

// `description` renders on the right of a palette row, so the keyboard route to a destination is
// learnt from the mouse route to it.
const destinations: PaletteItem[] = [
	{
		name: "home",
		title: "Home",
		description: formatShortcutLabel({ key: "h", ctrl: true, shift: true }),
		icon: icons.home,
		action: () => go("Home"),
	},
	{
		name: "orders",
		title: "Orders",
		description: formatShortcutLabel({ key: "o", ctrl: true, shift: true }),
		icon: icons.orders,
		action: () => go("Orders"),
	},
	{
		name: "products",
		title: "Products",
		description: formatShortcutLabel({ key: "p", ctrl: true, shift: true }),
		icon: icons.products,
		action: () => go("Products"),
	},
	{
		name: "inventory",
		title: "Inventory",
		description: formatShortcutLabel({ key: "i", ctrl: true, shift: true }),
		icon: icons.inventory,
		action: () => go("Inventory"),
	},
	{
		name: "navigation",
		title: "Navigation",
		description: formatShortcutLabel({ key: "m", ctrl: true, shift: true }),
		icon: icons.navigation,
		action: () => go("Navigation"),
	},
	{
		name: "footer",
		title: "Footer",
		description: formatShortcutLabel({ key: "f", ctrl: true, shift: true }),
		icon: icons.footer,
		action: () => go("Footer"),
	},
]

const actions: PaletteItem[] = [
	{
		name: "add-product",
		title: "Add product",
		description: formatShortcutLabel({ key: "a", ctrl: true, shift: true }),
		icon: icons.add,
		action: openAddProduct,
	},
	{
		name: "view-storefront",
		title: "View storefront",
		icon: icons.storefront,
		action: () => window.open("/", "_blank"),
	},
	{
		name: "shortcuts",
		title: "Keyboard shortcuts",
		description: formatShortcutLabel({ key: "/", ctrl: true }),
		icon: icons.keyboard,
		action: () => {
			showShortcuts.value = true
		},
	},
]

// One entry per settings tab, mirroring AppSettingsDialog's slugs, so the palette reaches every
// panel rather than only the two the dialog opens on.
const settingsTabs: PaletteItem[] = [
	{
		name: "settings-profile",
		title: "Profile",
		icon: icons.profile,
		action: () => openSettings("profile"),
	},
	{
		name: "settings-appearance",
		title: "Appearance",
		icon: icons.appearance,
		action: () => openSettings("appearance"),
	},
	{
		name: "settings-store",
		title: "Store details",
		icon: icons.store,
		action: () => openSettings("store"),
	},
	{
		name: "settings-shipping",
		title: "Shipping & returns",
		icon: icons.shipping,
		action: () => openSettings("shipping"),
	},
	{
		name: "settings-payments",
		title: "Payments",
		icon: icons.payments,
		action: () => openSettings("payments"),
	},
	{
		name: "settings-footer",
		title: "Footer & social",
		icon: icons.footer,
		action: () => openSettings("footer"),
	},
	{
		name: "settings-advanced",
		title: "Advanced",
		icon: icons.advanced,
		action: () => openSettings("advanced"),
	},
]

const themes: PaletteItem[] = [
	{
		name: "theme-light",
		title: "Light mode",
		icon: icons.light,
		action: () => setTheme("light"),
	},
	{
		name: "theme-dark",
		title: "Dark mode",
		icon: icons.dark,
		action: () => setTheme("dark"),
	},
	{
		name: "theme-system",
		title: "System theme",
		icon: icons.system,
		action: () => setTheme("system"),
	},
]

const productSearch = useCall<{ products: ProductRow[] }>({
	url: "/api/v2/method/ls_shop.api.admin.catalog.get_products",
	params: () => ({ search: searchQuery.value, page_length: 5 }),
	immediate: false,
})

const orderSearch = useCall<{ orders: OrderRow[] }>({
	url: "/api/v2/method/ls_shop.api.admin.orders.get_orders",
	params: () => ({ search: searchQuery.value, page_length: 5 }),
	immediate: false,
})

// CommandPalette never filters - that is the caller's job - so the static entries are matched
// here and the record lookups are debounced into the same list.
let searchTimer: ReturnType<typeof setTimeout>
watch(searchQuery, (query) => {
	clearTimeout(searchTimer)
	if (!query.trim()) return
	searchTimer = setTimeout(async () => {
		await Promise.all([productSearch.submit(), orderSearch.submit()])
	}, 250)
})

// ponytail: beta-37's CommandPalette puts `v-model` on headlessui's ComboboxInput, which only
// emits `change` - so `update:searchQuery` never fires and the palette cannot report what was
// typed. Reading the native input event is the bridge; delete it once the upstream emit lands.
useEventListener(document, "input", (event: Event) => {
	const target = event.target as HTMLElement | null
	if (!showPalette.value || target?.getAttribute("role") !== "combobox") return
	searchQuery.value = (target as HTMLInputElement).value
})

function matches(items: PaletteItem[]) {
	const query = searchQuery.value.trim().toLowerCase()
	if (!query) return items
	return items.filter((item) => item.title.toLowerCase().includes(query))
}

const productMatches = computed<PaletteItem[]>(() =>
	searchQuery.value.trim()
		? (productSearch.data?.products ?? []).map((product) => ({
				name: `product-${product.name}`,
				title: product.title,
				description: product.collection,
				icon: icons.products,
				action: () =>
					router.push({ name: "Product", params: { name: product.name } }),
			}))
		: [],
)

const orderMatches = computed<PaletteItem[]>(() =>
	searchQuery.value.trim()
		? (orderSearch.data?.orders ?? []).map((order) => ({
				name: `order-${order.name}`,
				title: order.name,
				description: order.customer,
				icon: icons.orders,
				action: () =>
					router.push({ name: "Order", params: { name: order.name } }),
			}))
		: [],
)

const groups = computed(() =>
	[
		{ title: "Go to", items: matches(destinations) },
		{ title: "Actions", items: matches(actions) },
		{ title: "Settings", items: matches(settingsTabs) },
		{ title: "Theme", items: matches(themes) },
		{ title: "Products", items: productMatches.value },
		{ title: "Orders", items: orderMatches.value },
	]
		.filter((group) => group.items.length)
		.map((group) => ({ ...group, component: markRaw(CommandPaletteItem) })),
)

function run(item: PaletteItem) {
	item.action()
}

// One registry: every shortcut declares its own description and group, which is what the
// shortcuts modal lists - so the help stays in step with the bindings by construction.
useShortcut([
	{
		key: "k",
		ctrl: true,
		description: "Open command palette",
		group: "General",
		handler: () => {
			showPalette.value = true
		},
	},
	{
		key: "/",
		ctrl: true,
		description: "Show keyboard shortcuts",
		group: "General",
		// The palette and the settings dialog are both `[role=dialog]`, and help should still
		// answer from inside them.
		allowInDialog: true,
		handler: () => {
			showShortcuts.value = true
		},
	},
	{
		key: ",",
		ctrl: true,
		description: "Open settings",
		group: "General",
		handler: () => openSettings(),
	},
	{
		key: "l",
		ctrl: true,
		shift: true,
		description: "Toggle light / dark theme",
		group: "General",
		handler: () => setTheme(currentTheme.value === "dark" ? "light" : "dark"),
	},
	{
		key: "h",
		ctrl: true,
		shift: true,
		description: "Go to Home",
		group: "Navigation",
		handler: () => go("Home"),
	},
	{
		key: "o",
		ctrl: true,
		shift: true,
		description: "Go to Orders",
		group: "Navigation",
		handler: () => go("Orders"),
	},
	{
		key: "p",
		ctrl: true,
		shift: true,
		description: "Go to Products",
		group: "Navigation",
		handler: () => go("Products"),
	},
	{
		key: "i",
		ctrl: true,
		shift: true,
		description: "Go to Inventory",
		group: "Navigation",
		handler: () => go("Inventory"),
	},
	{
		key: "m",
		ctrl: true,
		shift: true,
		description: "Go to Navigation",
		group: "Navigation",
		handler: () => go("Navigation"),
	},
	{
		key: "f",
		ctrl: true,
		shift: true,
		description: "Go to Footer",
		group: "Navigation",
		handler: () => go("Footer"),
	},
	{
		key: "a",
		ctrl: true,
		shift: true,
		description: "Add product",
		group: "Catalog",
		handler: () => openAddProduct(),
	},
])
</script>

<template>
	<CommandPalette
		v-model:show="showPalette"
		v-model:search-query="searchQuery"
		:groups="groups"
		@select="run"
	/>
	<KeyboardShortcutsModal v-model:open="showShortcuts" />
</template>
