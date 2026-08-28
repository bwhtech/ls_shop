<script setup lang="ts">
import {
	SettingsContent,
	SettingsDialog,
	SettingsNavGroup,
	SettingsNavItem,
	SettingsPanel,
	SettingsSidebar,
} from "frappe-ui"
import { type Component, markRaw } from "vue"
import AdvancedSettings from "./AdvancedSettings.vue"
import AnalyticsSettings from "./AnalyticsSettings.vue"
import AppearanceSettings from "./AppearanceSettings.vue"
import FooterSettings from "./FooterSettings.vue"
import PaymentSettings from "./PaymentSettings.vue"
import ProfileSettings from "./ProfileSettings.vue"
import ShippingSettings from "./ShippingSettings.vue"
import StoreSettings from "./StoreSettings.vue"
import { activeSettingsTab, settingsTabs, showSettings } from "./index"

const panels: Record<string, Component> = {
	profile: markRaw(ProfileSettings),
	appearance: markRaw(AppearanceSettings),
	store: markRaw(StoreSettings),
	shipping: markRaw(ShippingSettings),
	payments: markRaw(PaymentSettings),
	analytics: markRaw(AnalyticsSettings),
	footer: markRaw(FooterSettings),
	advanced: markRaw(AdvancedSettings),
}

const tabGroups = ["Account", "Store", "Advanced"].map((label) => ({
	label,
	tabs: settingsTabs.filter((tab) => tab.group === label),
}))
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
			<SettingsPanel v-for="tab in settingsTabs" :key="tab.slug" :value="tab.slug">
				<component :is="panels[tab.slug]" />
			</SettingsPanel>
		</SettingsContent>
	</SettingsDialog>
</template>
