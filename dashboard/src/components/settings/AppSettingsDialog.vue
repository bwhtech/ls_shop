<script setup lang="ts">
import {
	SettingsContent,
	SettingsDialog,
	SettingsNavGroup,
	SettingsNavItem,
	SettingsPanel,
	SettingsSidebar,
} from "frappe-ui"
import { markRaw } from "vue"
import AppearanceSettings from "./AppearanceSettings.vue"
import ProfileSettings from "./ProfileSettings.vue"
import StoreSettings from "./StoreSettings.vue"
import { activeSettingsTab, showSettings } from "./index"

const tabs = [
	{
		label: "Profile",
		slug: "profile",
		icon: "lucide-circle-user",
		component: markRaw(ProfileSettings),
		group: "Account",
	},
	{
		label: "Appearance",
		slug: "appearance",
		icon: "lucide-palette",
		component: markRaw(AppearanceSettings),
		group: "Account",
	},
	{
		label: "Store details",
		slug: "store",
		icon: "lucide-store",
		component: markRaw(StoreSettings),
		group: "Store",
	},
]

const tabGroups = [
	{ label: "Account", tabs: tabs.filter((tab) => tab.group === "Account") },
	{ label: "Store", tabs: tabs.filter((tab) => tab.group === "Store") },
]
</script>

<template>
	<SettingsDialog v-model="showSettings" v-model:tab="activeSettingsTab" size="4xl">
		<SettingsSidebar>
			<SettingsNavGroup v-for="group in tabGroups" :key="group.label" :label="group.label">
				<SettingsNavItem v-for="tab in group.tabs" :key="tab.slug" :value="tab.slug">
					<template #prefix>
						<span :class="[tab.icon, 'size-4 shrink-0 text-ink-gray-6']" aria-hidden="true" />
					</template>
					{{ tab.label }}
				</SettingsNavItem>
			</SettingsNavGroup>
		</SettingsSidebar>

		<SettingsContent>
			<SettingsPanel v-for="tab in tabs" :key="tab.slug" :value="tab.slug">
				<component :is="tab.component" />
			</SettingsPanel>
		</SettingsContent>
	</SettingsDialog>
</template>
