<script setup lang="ts">
import { useNavMenu } from "@/composables/useNavMenu"
import { useElementSize } from "@vueuse/core"
import { Button, TabButtons } from "frappe-ui"
import { computed, ref } from "vue"

const { previewUrl, previewToken } = useNavMenu()

// Real widths, not pane widths. The storefront switches to its drawer menu below Tailwind's
// `lg` (1024px), and the pane left over next to the tree and inspector is narrower than that -
// so framing at pane width showed the mobile header under a button labelled "Desktop". The
// frame is rendered at these widths and scaled down to fit instead.
const VIEWPORTS = [
	{ label: "Desktop", value: "desktop", width: 1440 },
	{ label: "Mobile", value: "mobile", width: 390 },
]

const viewport = ref("desktop")

const frameWidth = computed(
	() =>
		VIEWPORTS.find((entry) => entry.value === viewport.value)?.width ?? 1440,
)

const stage = ref<HTMLElement | null>(null)
const { width: stageWidth, height: stageHeight } = useElementSize(stage)

// Only ever shrink: a 390px mobile frame blown up to fill a wide pane would be a lie about
// what the shopper sees.
const scale = computed(() =>
	stageWidth.value ? Math.min(1, stageWidth.value / frameWidth.value) : 1,
)

const frameHeight = computed(() =>
	scale.value ? Math.max(stageHeight.value / scale.value, 320) : 320,
)

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
		<div
			class="flex min-h-12 items-center justify-between gap-2 border-b border-outline-gray-1 px-5"
		>
			<TabButtons v-model="viewport" :buttons="VIEWPORTS" />
			<div class="flex min-w-0 items-center gap-2">
				<!-- The scale readout is the first thing to go when the pane is tight; the
				     actions are not optional. -->
				<span class="hidden shrink truncate text-sm text-ink-gray-5 xl:inline">
					{{ frameWidth }}px · {{ Math.round(scale * 100) }}%
				</span>
				<Button
					class="shrink-0"
					icon-left="lucide-rotate-cw"
					label="Refresh"
					@click="previewToken += 1"
				/>
				<Button
					class="shrink-0"
					icon-left="lucide-external-link"
					label="Open"
					@click="openStorefront"
				/>
			</div>
		</div>

		<div ref="stage" class="min-h-0 flex-1 overflow-hidden p-4">
			<iframe
				:key="viewport"
				:src="source"
				title="Storefront preview"
				class="origin-top-left rounded border border-outline-gray-2"
				:style="{
					width: `${frameWidth}px`,
					height: `${frameHeight}px`,
					transform: `scale(${scale})`,
				}"
			/>
		</div>
	</div>
</template>
