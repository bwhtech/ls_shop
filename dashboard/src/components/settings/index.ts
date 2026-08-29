import { ref } from "vue"

/** Global handle for the settings dialog, so any screen can open it without prop-drilling. */
export const showSettings = ref(false)
export const activeSettingsTab = ref("appearance")

export function openSettings(tab = "appearance") {
	activeSettingsTab.value = tab
	showSettings.value = true
}

export type SettingsTab = {
	label: string
	slug: string
	icon: string
	group: string
}

/** Panels are resolved in AppSettingsDialog, so the command palette can list every tab without pulling all eight into its chunk. */
export const settingsTabs: SettingsTab[] = [
	{
		label: "Profile",
		slug: "profile",
		icon: "lucide-circle-user",
		group: "Account",
	},
	{
		label: "Appearance",
		slug: "appearance",
		icon: "lucide-palette",
		group: "Account",
	},
	{
		label: "Store details",
		slug: "store",
		icon: "lucide-store",
		group: "Store",
	},
	{
		label: "Shipping & returns",
		slug: "shipping",
		icon: "lucide-truck",
		group: "Store",
	},
	{
		label: "Payments",
		slug: "payments",
		icon: "lucide-credit-card",
		group: "Store",
	},
	{
		label: "Analytics & tracking",
		slug: "analytics",
		icon: "lucide-chart-line",
		group: "Store",
	},
	{
		label: "Footer & social",
		slug: "footer",
		icon: "lucide-panel-bottom",
		group: "Store",
	},
	{
		label: "Advanced",
		slug: "advanced",
		icon: "lucide-settings-2",
		group: "Advanced",
	},
]
