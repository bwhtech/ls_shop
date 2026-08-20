<script setup lang="ts">
import { useNavMenu } from "@/composables/useNavMenu"
import { Button, TabButtons } from "frappe-ui"
import { computed, ref } from "vue"

const { previewUrl, previewToken } = useNavMenu()

const VIEWPORTS = [
	{ label: "Desktop", value: "desktop" },
	{ label: "Mobile", value: "mobile" },
]

const viewport = ref("desktop")

function openStorefront() {
	window.open(previewUrl.value, "_blank", "noopener")
}

// The frame renders the real storefront, so it cannot be told the menu moved - it has to fetch
// again. The token changes on every mutation, which changes the src, which reloads the frame.
const source = computed(() => {
	const separator = previewUrl.value.includes("?") ? "&" : "?"
	return `${previewUrl.value}${separator}nav-preview=${previewToken.value}`
})
</script>

<template>
	<div class="flex h-full flex-col bg-surface-gray-1">
		<div class="flex min-h-12 items-center justify-between gap-2 border-b border-outline-gray-1 px-5">
			<TabButtons v-model="viewport" :buttons="VIEWPORTS" />
			<div class="flex items-center gap-2">
				<Button
					icon-left="lucide-rotate-cw"
					label="Refresh"
					@click="previewToken += 1"
				/>
				<Button
					icon-left="lucide-external-link"
					label="Open"
					@click="openStorefront"
				/>
			</div>
		</div>

		<div class="min-h-0 flex-1 overflow-auto p-4">
			<!-- The mobile frame is a real narrow viewport, not a scaled-down desktop one: the
			     storefront swaps to a different menu below its breakpoint, and that drawer is
			     exactly what needs checking here. -->
			<iframe
				:key="viewport"
				:src="source"
				title="Storefront preview"
				class="mx-auto h-full rounded border border-outline-gray-2"
				:class="viewport === 'mobile' ? 'w-[390px]' : 'w-full'"
			/>
		</div>
	</div>
</template>
