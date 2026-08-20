<script setup lang="ts">
import { useElementSize } from "@vueuse/core"
import { Button, TabButtons } from "frappe-ui"
import { computed, ref } from "vue"

const props = defineProps<{
	/** Bumped by the page after every save, to pull the rendered footer again. */
	token: number
}>()

const collapsed = defineModel<boolean>("collapsed", { required: true })

// Framed at a real storefront width and scaled down, not reflowed to the pane: a footer given
// only the pane's width collapses to its mobile stack and shows a layout no shopper sees.
const FRAME_WIDTH = 1440

const LANGUAGES = [
	{ label: "English", value: "en" },
	{ label: "العربية", value: "ar" },
]

const language = ref("en")
const reloadToken = ref(0)

const stage = ref<HTMLElement | null>(null)
const { width: stageWidth, height: stageHeight } = useElementSize(stage)

const scale = computed(() =>
	stageWidth.value ? Math.min(1, stageWidth.value / FRAME_WIDTH) : 1,
)

// The frame is as tall as the stage divided by the scale, so the scaled result exactly fills
// the band rather than leaving a gap or overflowing it.
const frameHeight = computed(() =>
	scale.value ? Math.max(stageHeight.value / scale.value, 240) : 240,
)

const source = computed(
	() =>
		`/footer_editor_preview?lang=${language.value}&t=${props.token}-${reloadToken.value}`,
)
</script>

<template>
	<div class="shrink-0 border-t border-outline-gray-1 bg-surface-gray-1">
		<div class="flex min-h-11 items-center justify-between gap-2 px-3 sm:px-5">
			<div class="flex items-center gap-2">
				<Button
					variant="ghost"
					:icon-left="collapsed ? 'lucide-chevron-up' : 'lucide-chevron-down'"
					:label="collapsed ? 'Show footer preview' : 'Footer preview'"
					@click="collapsed = !collapsed"
				/>
				<TabButtons v-if="!collapsed" v-model="language" :buttons="LANGUAGES" />
			</div>

			<Button
				v-if="!collapsed"
				icon-left="lucide-rotate-cw"
				label="Refresh"
				@click="reloadToken += 1"
			/>
		</div>

		<div v-if="!collapsed" class="px-3 pb-3 sm:px-5">
			<div
				ref="stage"
				class="h-64 overflow-hidden rounded-4 border border-outline-gray-2 bg-surface-base"
			>
				<iframe
					:key="language"
					:src="source"
					title="Footer preview"
					class="origin-top-left border-0"
					:style="{
						width: `${FRAME_WIDTH}px`,
						height: `${frameHeight}px`,
						transform: `scale(${scale})`,
					}"
				/>
			</div>
		</div>
	</div>
</template>
