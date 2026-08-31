<script setup lang="ts">
import AppCommandPalette from "@/components/AppCommandPalette.vue"
import { showPalette, showShortcuts } from "@/components/commandPalette"
import { openSettings } from "@/components/settings"
import AppSettingsDialog from "@/components/settings/AppSettingsDialog.vue"
import {
	type NavDestination,
	colorSchemeOptions,
	navSections,
} from "@/navigation"
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
import { useRoute, useRouter } from "vue-router"

const store = useCall<Record<string, string>>({
	url: "/api/v2/method/ls_shop.api.admin.settings.get_store_settings",
})

const storeName = computed(() => store.data?.store_name || "Your store")

const { colorScheme, setColorScheme } = useColorScheme()

const router = useRouter()
const currentRoute = useRoute()

// SidebarItem's own inference matches the route name exactly, which drops the
// highlight on detail pages. Detail routes are nested under their section, so
// the shared matched record keeps the section lit while drilled in.
function isDestinationActive(destination: NavDestination) {
	const sectionRecord = router.resolve({ name: destination.route }).matched[0]
	return currentRoute.matched.some(
		(record) => record.path === sectionRecord?.path,
	)
}

function themeCheckmark(theme: ColorScheme) {
	if (colorScheme.value !== theme) return null
	return h("span", { class: "lucide-check size-4 text-ink-gray-6" })
}

const menuItems = computed(() => [
	{
		icon: "lucide-settings",
		label: "Settings",
		onClick: () => openSettings("store"),
	},
	{
		icon: "lucide-moon",
		label: "Toggle theme",
		submenu: colorSchemeOptions.map((option) => ({
			label: option.label,
			icon: option.icon,
			slots: { suffix: () => themeCheckmark(option.value) },
			onClick: () => setColorScheme(option.value),
		})),
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
</script>

<template>
	<DesktopShell :scroll="false" class="app-shell">
		<template #sidebar>
			<Sidebar disable-collapse width="14rem">
				<SidebarHeader
					:title="storeName"
					:subtitle="store.data?.contact_email || undefined"
					:logo="store.data?.brand_logo || undefined"
					:menu-items="menuItems"
				/>

				<div class="shrink-0 px-2 pb-2">
					<Button
						class="w-full !justify-start"
						variant="ghost"
						icon-left="lucide-search"
						@click="showPalette = true"
					>
						<span class="flex-1 text-start">Search</span>
						<template #suffix>
							<KeyboardShortcut combo="Mod+K" bg />
						</template>
					</Button>
				</div>

				<ScrollArea class="min-h-0 flex-1" viewport-class="px-2 pb-6">
					<nav aria-label="Main">
						<div v-for="section in navSections" :key="section.label" class="mb-3">
							<SidebarLabel v-if="section.label">{{ section.label }}</SidebarLabel>
							<div class="mt-0.5 space-y-0.5">
								<SidebarItem
									v-for="destination in section.destinations"
									:key="destination.route"
									:to="{ name: destination.route }"
									:icon="destination.icon"
									:label="destination.label"
									:active="isDestinationActive(destination)"
								/>
							</div>
						</div>
					</nav>
				</ScrollArea>
			</Sidebar>
		</template>

		<slot />
		<AppSettingsDialog />
		<AppCommandPalette />
	</DesktopShell>
</template>

<style scoped>
/* The app root paints sidebar and base the same colour in dark mode, so the content area needs its own surface and divider. */
/* SidebarLabel hardcodes text-base (14px), larger than the 13px links it groups. */
.app-shell :deep([data-slot="sidebar-label"] h3) {
	@apply text-xs font-medium text-ink-gray-5;
}

.app-shell :deep([data-slot="desktop-shell-content"]) {
	@apply border-l border-outline-gray-1 bg-surface-base;
}
</style>
