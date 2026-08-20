<script setup lang="ts">
import { openSettings } from "@/components/settings"
import { Dropdown, useTheme } from "frappe-ui"
import { computed, h } from "vue"

const { currentTheme, setTheme } = useTheme()

/** A tick against whichever theme is active, the way Gameplan marks the current choice. */
function themeCheckmark(theme: string) {
	if (currentTheme.value !== theme) return null
	return h("span", { class: "lucide-check size-4 text-ink-gray-6" })
}

const options = computed(() => [
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
				onClick: () => setTheme("light"),
			},
			{
				label: "Dark Mode",
				icon: "lucide-moon",
				slots: { suffix: () => themeCheckmark("dark") },
				onClick: () => setTheme("dark"),
			},
			{
				label: "System Default",
				icon: "lucide-monitor",
				slots: { suffix: () => themeCheckmark("system") },
				onClick: () => setTheme("system"),
			},
		],
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
	<Dropdown :options="options">
		<template #default="{ open }">
			<slot name="trigger" :open="open" />
		</template>
	</Dropdown>
</template>
