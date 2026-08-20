<script setup lang="ts">
import AppCommandPalette from "@/components/AppCommandPalette.vue"
import StoreDropdown from "@/components/StoreDropdown.vue"
import { openSettings } from "@/components/settings"
import AppSettingsDialog from "@/components/settings/AppSettingsDialog.vue"
import {
	Button,
	DesktopShell,
	ScrollArea,
	Sidebar,
	SidebarItem,
	SidebarLabel,
	useCall,
} from "frappe-ui"
import { computed } from "vue"

const store = useCall<Record<string, string>>({
	url: "/api/v2/method/ls_shop.api.admin.settings.get_store_settings",
})

const storeName = computed(() => store.data?.store_name || "Your store")

const sections = [
	{
		label: "Store",
		items: [
			{ label: "Orders", route: "Orders", icon: "lucide-receipt" },
			{ label: "Products", route: "Products", icon: "lucide-package" },
			{ label: "Inventory", route: "Inventory", icon: "lucide-boxes" },
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
				<div class="shrink-0 p-1.5">
					<StoreDropdown>
						<template #trigger="{ open }">
							<button
								type="button"
								class="flex w-full items-center gap-2 rounded px-1.5 py-1.5 text-left hover:bg-surface-gray-2"
								:class="{ 'bg-surface-gray-2': open }"
							>
								<div
									class="grid size-7 shrink-0 place-items-center rounded bg-surface-gray-3 text-sm text-ink-gray-7"
								>
									{{ storeName.slice(0, 1) }}
								</div>
								<span class="truncate text-base font-medium text-ink-gray-8">
									{{ storeName }}
								</span>
								<span
									class="lucide-chevrons-up-down ml-auto size-4 shrink-0 text-ink-gray-5"
									aria-hidden="true"
								/>
							</button>
						</template>
					</StoreDropdown>
				</div>

				<ScrollArea class="min-h-0 flex-1" viewport-class="px-2 pb-6">
					<template v-for="section in sections" :key="section.label">
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
					</template>
				</ScrollArea>

				<div class="shrink-0 border-t border-outline-gray-1 p-2">
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
