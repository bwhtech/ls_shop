<script setup lang="ts">
import {
	useElementSize,
	useEventListener,
	useStorage,
	useWindowSize,
} from "@vueuse/core"
import { Button, TabButtons } from "frappe-ui"
import { computed, ref } from "vue"

import { useLocale } from "@/composables/useLocale"

const props = defineProps<{
	token: number
	path: string
	title: string
	selector: string
}>()

const collapsed = defineModel<boolean>("collapsed", { required: true })

const FRAME_WIDTH = 1440

const LANGUAGES = [
	{ label: "English", value: "en" },
	{ label: "العربية", value: "ar" },
]

const { language: sessionLanguage } = useLocale()

// The preview opens in the language the session is actually in - the storefront renders its own
// direction from that - falling back to English for a language the storefront chrome cannot preview.
const language = ref(
	LANGUAGES.some((option) => option.value === sessionLanguage)
		? sessionLanguage
		: "en",
)
const reloadToken = ref(0)

const stage = ref<HTMLElement | null>(null)
const { width: stageWidth } = useElementSize(stage)
const { height: windowHeight } = useWindowSize()

const FALLBACK_FRAME_HEIGHT = 560
const MAX_STAGE_HEIGHT = 420
const MIN_STAGE_HEIGHT = 160
const RESIZE_STEP = 40
// A hovered mega-menu opens under the navbar, so a frame ending at the chrome bottom clips it out of existence.
const DROPDOWN_HEADROOM = 460

const contentHeight = ref(0)

const scale = computed(() =>
	stageWidth.value ? Math.min(1, stageWidth.value / FRAME_WIDTH) : 1,
)

const headroom = computed(() =>
	props.selector === "header" ? DROPDOWN_HEADROOM : 0,
)

// Sizing the frame to the pane crops the footer-bottom strip, so it is driven by the rendered footer.
const frameHeight = computed(
	() => (contentHeight.value || FALLBACK_FRAME_HEIGHT) + headroom.value,
)

// The editor board above must survive the drag, so the pane can never own the whole viewport.
const maxStageHeight = computed(() =>
	Math.max(MIN_STAGE_HEIGHT, Math.round(windowHeight.value * 0.7)),
)

// Zero means untouched: the pane keeps fitting itself to the chrome until the user drags it.
const storedStageHeight = useStorage(`ls-shop-preview-height:${props.path}`, 0)

const stageHeight = computed(() =>
	storedStageHeight.value
		? Math.min(
				Math.max(storedStageHeight.value, MIN_STAGE_HEIGHT),
				maxStageHeight.value,
			)
		: Math.min(frameHeight.value * scale.value, MAX_STAGE_HEIGHT),
)

const resizing = ref(false)
let resizeOrigin = 0
let resizeBaseHeight = 0

function resizeTo(height: number) {
	storedStageHeight.value = Math.min(
		Math.max(Math.round(height), MIN_STAGE_HEIGHT),
		maxStageHeight.value,
	)
}

function startResize(event: PointerEvent) {
	resizing.value = true
	resizeOrigin = event.clientY
	resizeBaseHeight = stageHeight.value
}

useEventListener(window, "pointermove", (event: PointerEvent) => {
	if (!resizing.value) return
	event.preventDefault()
	resizeTo(resizeBaseHeight + (resizeOrigin - event.clientY))
})

useEventListener(window, "pointerup", () => {
	resizing.value = false
})

function measureFrame(event: Event) {
	const frame = event.target as HTMLIFrameElement
	const previewDocument = frame.contentDocument
	// Measured off the chrome itself: a full-height themed page's scrollHeight would hang an empty storefront under the navbar.
	const chrome = previewDocument?.querySelector(props.selector)
	contentHeight.value = chrome
		? Math.ceil(chrome.getBoundingClientRect().bottom)
		: (previewDocument?.documentElement?.scrollHeight ?? 0)
}

const source = computed(
	() =>
		`${props.path}?lang=${language.value}&t=${props.token}-${reloadToken.value}`,
)
</script>

<template>
	<div
		class="shrink-0 border-t border-outline-gray-1 bg-surface-gray-1"
		:class="resizing && 'select-none'"
	>
		<div class="flex min-h-11 items-center justify-between gap-2 px-3 sm:px-5">
			<div class="flex items-center gap-2">
				<Button
					v-if="!collapsed"
					variant="ghost"
					icon="lucide-grip-horizontal"
					class="cursor-ns-resize"
					:aria-label="`Resize ${title.toLowerCase()}`"
					@pointerdown="startResize"
					@keydown.up.prevent="resizeTo(stageHeight + RESIZE_STEP)"
					@keydown.down.prevent="resizeTo(stageHeight - RESIZE_STEP)"
				/>
				<Button
					variant="ghost"
					:icon-left="collapsed ? 'lucide-chevron-up' : 'lucide-chevron-down'"
					:label="collapsed ? `Show ${title.toLowerCase()}` : title"
					@click="collapsed = !collapsed"
				/>
				<TabButtons v-if="!collapsed" v-model="language" :options="LANGUAGES" />
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
				class="overflow-y-auto rounded-4 border border-outline-gray-2 bg-surface-base"
				:style="{ height: `${stageHeight}px` }"
			>
				<iframe
					:key="language"
					:src="source"
					:title="title"
					class="origin-top-left border-0 rtl:origin-top-right"
					:style="{
						width: `${FRAME_WIDTH}px`,
						height: `${frameHeight}px`,
						transform: `scale(${scale})`,
					}"
					@load="measureFrame"
				/>
			</div>
		</div>
	</div>
</template>
