<script setup lang="ts">
import AppCommandPalette from "@/components/AppCommandPalette.vue"
import { showPalette, showShortcuts } from "@/components/commandPalette"
import { openSettings } from "@/components/settings"
import AppSettingsDialog from "@/components/settings/AppSettingsDialog.vue"
import {
	Button,
	type ColorScheme,
	DesktopShell,
	KeyboardShortcut,
	ScrollArea,
	Sidebar,
	SidebarHeader,
	SidebarItem,
	SidebarLabel,
	useCall,
	useColorScheme,
} from "frappe-ui"
import { computed, h } from "vue"

const store = useCall<Record<string, string>>({
	url: "/api/v2/method/ls_shop.api.admin.settings.get_store_settings",
})

const storeName = computed(() => store.data?.store_name || "Your store")

const { colorScheme, setColorScheme } = useColorScheme()

/** A tick against whichever theme is active, the way Gameplan marks the current choice. */
function themeCheckmark(theme: ColorScheme) {
	if (colorScheme.value !== theme) return null
	return h("span", { class: "lucide-check size-4 text-ink-gray-6" })
}

// SidebarHeader hands `menu-items` straight to Dropdown, so the nested theme submenu Dropdown
// already supports survives the move off the hand-rolled trigger.
const menuItems = computed(() => [
	{
		icon: "lucide-settings",
		label: "Settings",
		onClick: () => openSettings("store"),
	},
	{
		icon: "lucide-moon",
		label: "Toggle theme",
		submenu: [
			{
				label: "Light Mode",
				icon: "lucide-sun",
				slots: { suffix: () => themeCheckmark("light") },
				onClick: () => setColorScheme("light"),
			},
			{
				label: "Dark Mode",
				icon: "lucide-moon",
				slots: { suffix: () => themeCheckmark("dark") },
				onClick: () => setColorScheme("dark"),
			},
			{
				label: "System Default",
				icon: "lucide-monitor",
				slots: { suffix: () => themeCheckmark("system") },
				onClick: () => setColorScheme("system"),
			},
		],
	},
	{
		icon: "lucide-keyboard",
		label: "Keyboard shortcuts",
		onClick: () => {
			showShortcuts.value = true
		},
	},
	{
		icon: "lucide-external-link",
		label: "View storefront",
		onClick: () => window.open("/", "_blank"),
	},
	{
		icon: "lucide-log-out",
		label: "Log out",
		onClick: () => {
			window.location.href = "/api/method/logout"
		},
	},
])

const sections = [
	{
		label: "Overview",
		items: [{ label: "Home", route: "Home", icon: "lucide-house" }],
	},
	{
		label: "Sales",
		items: [{ label: "Orders", route: "Orders", icon: "lucide-receipt" }],
	},
	{
		label: "Catalog",
		items: [
			{ label: "Products", route: "Products", icon: "lucide-package" },
			{ label: "Inventory", route: "Inventory", icon: "lucide-boxes" },
		],
	},
	{
		label: "Storefront",
		items: [
			{ label: "Navigation", route: "Navigation", icon: "lucide-menu" },
			{ label: "Footer", route: "Footer", icon: "lucide-panel-bottom" },
		],
	},
]
</script>

<template>
	<!-- scroll=false: each page owns its own scroll region, so a list scrolls independently of
	     its sticky header instead of the whole shell scrolling. -->
	<DesktopShell :scroll="false" class="app-shell">
		<template #sidebar>
			<Sidebar disable-collapse width="14rem">
				<SidebarHeader
					:title="storeName"
					:subtitle="store.data?.contact_email || undefined"
					:logo="store.data?.brand_logo || undefined"
					:menu-items="menuItems"
				/>

				<ScrollArea class="min-h-0 flex-1" viewport-class="px-2 pb-6">
					<div v-for="section in sections" :key="section.label" class="mb-3">
						<SidebarLabel>{{ section.label }}</SidebarLabel>
						<nav class="mt-0.5 space-y-0.5">
							<SidebarItem
								v-for="item in section.items"
								:key="item.route"
								:to="{ name: item.route }"
							>
								<template #prefix>
									<span
										:class="[item.icon, 'size-4 shrink-0 text-ink-gray-6']"
										aria-hidden="true"
									/>
								</template>
								<span class="truncate text-sm">{{ item.label }}</span>
							</SidebarItem>
						</nav>
					</div>
				</ScrollArea>

				<div class="shrink-0 space-y-0.5 border-t border-outline-gray-1 p-2">
					<Button
						class="w-full !justify-start"
						variant="ghost"
						icon-left="lucide-search"
						@click="showPalette = true"
					>
						<span class="flex-1 text-left">Search</span>
						<template #suffix>
							<KeyboardShortcut combo="Mod+K" bg />
						</template>
					</Button>
					<Button
						class="w-full !justify-start"
						variant="ghost"
						icon-left="lucide-settings"
						label="Settings"
						@click="openSettings()"
					/>
				</div>
			</Sidebar>
		</template>

		<slot />
		<AppSettingsDialog />
		<AppCommandPalette />
	</DesktopShell>
</template>

<style scoped>
/* The sidebar column is painted by the app root (bg-surface-sidebar over bg-surface-base),
   which in dark mode resolves to the same colour as the pages. The rule gives the content
   area its own surface plus the divider that separates it from the sidebar. */
.app-shell :deep([data-slot="desktop-shell-content"]) {
	@apply border-l border-outline-gray-1 bg-surface-base;
}
</style>
