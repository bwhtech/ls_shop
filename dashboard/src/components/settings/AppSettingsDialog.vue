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
import AdvancedSettings from "./AdvancedSettings.vue"
import AppearanceSettings from "./AppearanceSettings.vue"
import FooterSettings from "./FooterSettings.vue"
import PaymentSettings from "./PaymentSettings.vue"
import ProfileSettings from "./ProfileSettings.vue"
import ShippingSettings from "./ShippingSettings.vue"
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
	{
		label: "Shipping & returns",
		slug: "shipping",
		icon: "lucide-truck",
		component: markRaw(ShippingSettings),
		group: "Store",
	},
	{
		label: "Payments",
		slug: "payments",
		icon: "lucide-credit-card",
		component: markRaw(PaymentSettings),
		group: "Store",
	},
	{
		label: "Footer & social",
		slug: "footer",
		icon: "lucide-panel-bottom",
		component: markRaw(FooterSettings),
		group: "Store",
	},
	{
		label: "Advanced",
		slug: "advanced",
		icon: "lucide-settings-2",
		component: markRaw(AdvancedSettings),
		group: "Advanced",
	},
]

const tabGroups = [
	{ label: "Account", tabs: tabs.filter((tab) => tab.group === "Account") },
	{ label: "Store", tabs: tabs.filter((tab) => tab.group === "Store") },
	{ label: "Advanced", tabs: tabs.filter((tab) => tab.group === "Advanced") },
]
</script>

<template>
	<!-- shortcut=false: the library's built-in Cmd/Ctrl+Shift+, is a raw key listener that fires
	     while a search box has focus and never shows up in KeyboardShortcutsDialog. Our own
	     Mod+Comma is registered with the rest, so the help stays honest. -->
	<SettingsDialog v-model:open="showSettings" v-model:tab="activeSettingsTab" :shortcut="false">
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
