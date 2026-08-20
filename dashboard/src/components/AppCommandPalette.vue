<script setup lang="ts">
import { openAddProduct } from "@/components/addProduct"
import { showPalette, showShortcuts } from "@/components/commandPalette"
import { openSettings } from "@/components/settings"
import type { OrderRow, ProductRow } from "@/types"
import {
	KeyboardShortcut,
	type KeyboardShortcutCombo,
	KeyboardShortcutsDialog,
	useCall,
	useColorScheme,
	useKeyboardShortcut,
} from "frappe-ui"
import {
	CommandPalette,
	CommandPaletteEmpty,
	CommandPaletteGroup,
	CommandPaletteInput,
	CommandPaletteItem,
	CommandPaletteList,
	type CommandPaletteValue,
} from "frappe-ui/experimental"
import { computed, ref, watch } from "vue"
import { useRouter } from "vue-router"

type PaletteItem = {
	name: string
	title: string
	description?: string
	shortcut?: KeyboardShortcutCombo
	icon: string
	action: () => void
}

const router = useRouter()
const { setColorScheme, toggleColorScheme } = useColorScheme()

const searchQuery = ref("")

function go(route: string) {
	// A navigation shortcut is reachable from inside the palette, so the palette has to get out
	// of the way once it has been used to leave the current screen.
	showPalette.value = false
	router.push({ name: route })
}

// The shortcut chip rides on the row, so the keyboard route to a destination is learnt from
// the mouse route to it.
const destinations: PaletteItem[] = [
	{
		name: "home",
		title: "Home",
		shortcut: "Mod+Shift+H",
		icon: "lucide-house",
		action: () => go("Home"),
	},
	{
		name: "orders",
		title: "Orders",
		shortcut: "Mod+Shift+O",
		icon: "lucide-receipt",
		action: () => go("Orders"),
	},
	{
		name: "products",
		title: "Products",
		shortcut: "Mod+Shift+P",
		icon: "lucide-package",
		action: () => go("Products"),
	},
	{
		name: "inventory",
		title: "Inventory",
		shortcut: "Mod+Shift+U",
		icon: "lucide-boxes",
		action: () => go("Inventory"),
	},
	{
		name: "navigation",
		title: "Navigation",
		shortcut: "Mod+Shift+M",
		icon: "lucide-menu",
		action: () => go("Navigation"),
	},
	{
		name: "footer",
		title: "Footer",
		shortcut: "Mod+Shift+F",
		icon: "lucide-panel-bottom",
		action: () => go("Footer"),
	},
]

const actions: PaletteItem[] = [
	{
		name: "add-product",
		title: "Add product",
		shortcut: "Mod+Shift+A",
		icon: "lucide-plus",
		action: openAddProduct,
	},
	{
		name: "view-storefront",
		title: "View storefront",
		icon: "lucide-external-link",
		action: () => window.open("/", "_blank"),
	},
	{
		name: "shortcuts",
		title: "Keyboard shortcuts",
		shortcut: "Mod+Slash",
		icon: "lucide-keyboard",
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
		icon: "lucide-circle-user",
		action: () => openSettings("profile"),
	},
	{
		name: "settings-appearance",
		title: "Appearance",
		icon: "lucide-palette",
		action: () => openSettings("appearance"),
	},
	{
		name: "settings-store",
		title: "Store details",
		icon: "lucide-store",
		action: () => openSettings("store"),
	},
	{
		name: "settings-shipping",
		title: "Shipping & returns",
		icon: "lucide-truck",
		action: () => openSettings("shipping"),
	},
	{
		name: "settings-payments",
		title: "Payments",
		icon: "lucide-credit-card",
		action: () => openSettings("payments"),
	},
	{
		name: "settings-footer",
		title: "Footer & social",
		icon: "lucide-panel-bottom",
		action: () => openSettings("footer"),
	},
	{
		name: "settings-advanced",
		title: "Advanced",
		icon: "lucide-settings-2",
		action: () => openSettings("advanced"),
	},
]

const colorSchemes: PaletteItem[] = [
	{
		name: "theme-light",
		title: "Light mode",
		icon: "lucide-sun",
		action: () => setColorScheme("light"),
	},
	{
		name: "theme-dark",
		title: "Dark mode",
		icon: "lucide-moon",
		action: () => setColorScheme("dark"),
	},
	{
		name: "theme-system",
		title: "System theme",
		icon: "lucide-monitor",
		action: () => setColorScheme("system"),
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

// `filterable="false"`: the record rows are already what the server decided matches, so a
// second client pass would drop them. The static entries are matched here instead.
let searchTimer: ReturnType<typeof setTimeout>
watch(searchQuery, (query) => {
	clearTimeout(searchTimer)
	if (!query.trim()) return
	searchTimer = setTimeout(async () => {
		await Promise.all([productSearch.submit(), orderSearch.submit()])
	}, 250)
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
				icon: "lucide-package",
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
				icon: "lucide-receipt",
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
		{ title: "Theme", items: matches(colorSchemes) },
		{ title: "Products", items: productMatches.value },
		{ title: "Orders", items: orderMatches.value },
	].filter((group) => group.items.length),
)

function runCommand(command: CommandPaletteValue) {
	const item = command as PaletteItem
	item.action()
}

// One registry: every shortcut declares its own description and group, which is what
// KeyboardShortcutsDialog lists - so the help stays in step with the bindings by construction.
useKeyboardShortcut([
	{
		combo: "Mod+K",
		description: "Open command palette",
		group: "General",
		// The palette answers from a focused field too, or it dies the moment any page's search
		// box has focus.
		allowInInput: true,
		handler: () => {
			showPalette.value = true
		},
	},
	{
		combo: "Mod+Slash",
		description: "Show keyboard shortcuts",
		group: "General",
		// The palette and the settings dialog are both `[role=dialog]`, and the palette holds
		// focus in its own input, so help needs both gates open to answer from inside them.
		allowInInput: true,
		allowInDialog: true,
		handler: () => {
			showShortcuts.value = true
		},
	},
	{
		combo: "Mod+Comma",
		description: "Open settings",
		group: "General",
		handler: () => openSettings(),
	},
	{
		combo: "Mod+Shift+L",
		description: "Toggle light / dark theme",
		group: "General",
		handler: () => toggleColorScheme(),
	},
	// Every combo below is drawn as a chip on its own palette row, and the palette holds focus in
	// its own input inside a dialog - so both gates stay open, or the chip would advertise a
	// shortcut that cannot fire from where it is being read.
	{
		combo: "Mod+Shift+H",
		description: "Go to Home",
		group: "Navigation",
		allowInInput: true,
		allowInDialog: true,
		handler: () => go("Home"),
	},
	{
		combo: "Mod+Shift+O",
		description: "Go to Orders",
		group: "Navigation",
		allowInInput: true,
		allowInDialog: true,
		handler: () => go("Orders"),
	},
	{
		combo: "Mod+Shift+P",
		description: "Go to Products",
		group: "Navigation",
		allowInInput: true,
		allowInDialog: true,
		handler: () => go("Products"),
	},
	{
		// Not Mod+Shift+I: that is the browser's own devtools shortcut on every platform, so the
		// keystroke is swallowed before the app ever sees it.
		combo: "Mod+Shift+U",
		description: "Go to Inventory",
		group: "Navigation",
		allowInInput: true,
		allowInDialog: true,
		handler: () => go("Inventory"),
	},
	{
		combo: "Mod+Shift+M",
		description: "Go to Navigation",
		group: "Navigation",
		allowInInput: true,
		allowInDialog: true,
		handler: () => go("Navigation"),
	},
	{
		combo: "Mod+Shift+F",
		description: "Go to Footer",
		group: "Navigation",
		allowInInput: true,
		allowInDialog: true,
		handler: () => go("Footer"),
	},
	{
		combo: "Mod+Shift+A",
		description: "Add product",
		group: "Catalog",
		allowInInput: true,
		allowInDialog: true,
		handler: () => {
			showPalette.value = false
			openAddProduct()
		},
	},
])
</script>

<template>
	<CommandPalette
		v-model:open="showPalette"
		v-model:query="searchQuery"
		:filterable="false"
		@select="runCommand"
	>
		<CommandPaletteInput placeholder="Search products, orders and commands" />

		<CommandPaletteList>
			<CommandPaletteGroup
				v-for="group in groups"
				:key="group.title"
				:label="group.title"
			>
				<CommandPaletteItem
					v-for="item in group.items"
					:key="item.name"
					:value="item"
				>
					<template #prefix>
						<span
							:class="[item.icon, 'mr-2 size-4 shrink-0 text-ink-gray-6']"
							aria-hidden="true"
						/>
					</template>
					{{ item.title }}
					<template v-if="item.shortcut || item.description" #suffix>
						<KeyboardShortcut v-if="item.shortcut" :combo="item.shortcut" />
						<span v-else class="text-sm text-ink-gray-5">
							{{ item.description }}
						</span>
					</template>
				</CommandPaletteItem>
			</CommandPaletteGroup>
		</CommandPaletteList>

		<CommandPaletteEmpty>No matches</CommandPaletteEmpty>
	</CommandPalette>

	<KeyboardShortcutsDialog v-model:open="showShortcuts" />
</template>
