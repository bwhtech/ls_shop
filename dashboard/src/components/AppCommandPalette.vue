<script setup lang="ts">
import { openSettings } from "@/components/settings"
import {
	CommandPalette,
	KeyboardShortcutsModal,
	useShortcut,
	useTheme,
} from "frappe-ui"
import { computed, ref } from "vue"
import { useRouter } from "vue-router"

const router = useRouter()
const { setTheme } = useTheme()

const showPalette = ref(false)
const showShortcuts = ref(false)

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
		handler: () => {
			showShortcuts.value = true
		},
	},
	{
		key: "o",
		ctrl: true,
		shift: true,
		description: "Go to Orders",
		group: "Navigation",
		handler: () => router.push({ name: "Orders" }),
	},
	{
		key: "p",
		ctrl: true,
		shift: true,
		description: "Go to Products",
		group: "Navigation",
		handler: () => router.push({ name: "Products" }),
	},
	{
		key: "i",
		ctrl: true,
		shift: true,
		description: "Go to Inventory",
		group: "Navigation",
		handler: () => router.push({ name: "Inventory" }),
	},
	{
		key: ",",
		ctrl: true,
		description: "Open settings",
		group: "General",
		handler: () => openSettings(),
	},
])

function go(route: string) {
	showPalette.value = false
	router.push({ name: route })
}

const groups = computed(() => [
	{
		title: "Go to",
		items: [
			{ title: "Orders", icon: "lucide-receipt", onClick: () => go("Orders") },
			{
				title: "Products",
				icon: "lucide-package",
				onClick: () => go("Products"),
			},
			{
				title: "Inventory",
				icon: "lucide-boxes",
				onClick: () => go("Inventory"),
			},
		],
	},
	{
		title: "Settings",
		items: [
			{
				title: "Store details",
				icon: "lucide-store",
				onClick: () => {
					showPalette.value = false
					openSettings("store")
				},
			},
			{
				title: "Profile",
				icon: "lucide-circle-user",
				onClick: () => {
					showPalette.value = false
					openSettings("profile")
				},
			},
			{
				title: "Light mode",
				icon: "lucide-sun",
				onClick: () => {
					showPalette.value = false
					setTheme("light")
				},
			},
			{
				title: "Dark mode",
				icon: "lucide-moon",
				onClick: () => {
					showPalette.value = false
					setTheme("dark")
				},
			},
		],
	},
])
</script>

<template>
	<CommandPalette v-model:show="showPalette" :groups="groups" />
	<KeyboardShortcutsModal v-model:open="showShortcuts" />
</template>
