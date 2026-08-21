<script setup lang="ts">
import { useElementSize } from "@vueuse/core"
import { Button, TabButtons } from "frappe-ui"
import { computed, ref } from "vue"

const props = defineProps<{
	/** Bumped by the page after every save, to pull the rendered chrome again. */
	token: number
	/** The www page rendering this piece of chrome, e.g. `/footer_editor_preview`. */
	path: string
	/** Shown on the toggle, e.g. "Footer preview". */
	title: string
	/** The chrome being previewed, e.g. `footer`. The pane is sized to it. */
	selector: string
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
const { width: stageWidth } = useElementSize(stage)

// Until the frame reports its own height. A themed footer runs past 500px, so a smaller guess
// would crop the first paint of every load.
const FALLBACK_FRAME_HEIGHT = 560
// Past this the pane would own the screen, so it scrolls instead.
const MAX_STAGE_HEIGHT = 420

const contentHeight = ref(0)

const scale = computed(() =>
	stageWidth.value ? Math.min(1, stageWidth.value / FRAME_WIDTH) : 1,
)

// Driven by the rendered footer, not by the pane. Sizing the frame to the pane instead cropped
// whatever did not fit - which was the whole footer-bottom strip, including the copyright line
// and payment images this very editor edits.
const frameHeight = computed(() => contentHeight.value || FALLBACK_FRAME_HEIGHT)

const stageHeight = computed(() =>
	Math.min(frameHeight.value * scale.value, MAX_STAGE_HEIGHT),
)

function measureFrame(event: Event) {
	const frame = event.target as HTMLIFrameElement
	const previewDocument = frame.contentDocument
	// Measured off the chrome itself, not the document: a header sits at the top of a full-height
	// themed page, so sizing to scrollHeight would hang an empty storefront under the navbar.
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
	<div class="shrink-0 border-t border-outline-gray-1 bg-surface-gray-1">
		<div class="flex min-h-11 items-center justify-between gap-2 px-3 sm:px-5">
			<div class="flex items-center gap-2">
				<Button
					variant="ghost"
					:icon-left="collapsed ? 'lucide-chevron-up' : 'lucide-chevron-down'"
					:label="collapsed ? `Show ${title.toLowerCase()}` : title"
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
				class="overflow-y-auto rounded border border-outline-gray-2 bg-surface-base"
				:style="{ height: `${stageHeight}px` }"
			>
				<iframe
					:key="language"
					:src="source"
					:title="title"
					class="origin-top-left border-0"
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
