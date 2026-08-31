<script setup lang="ts">
import { ScrollArea } from "frappe-ui"
import { computed, onBeforeUnmount, onMounted, ref } from "vue"

// ponytail: local fade wrapper because frappe-ui's ScrollArea ships overlay
// scrollbars only (no mask/fade capability) — delete it if `fadeEdges` lands upstream.

const props = withDefaults(
	defineProps<{
		orientation?: "vertical" | "horizontal" | "both"
		scrollHideDelay?: number
		viewportClass?: string
		fadeSize?: string
	}>(),
	{ orientation: "vertical", scrollHideDelay: 600, fadeSize: "1.5rem" },
)

const scrollAreaRef = ref<{ viewportElement: HTMLElement | null } | null>(null)

const fadeLeft = ref(false)
const fadeRight = ref(false)
const fadeTop = ref(false)
const fadeBottom = ref(false)

function updateFades() {
	const viewport = scrollAreaRef.value?.viewportElement
	if (!viewport) {
		return
	}

	// Sub-pixel layout keeps scrollLeft/scrollTop a fraction short of their maximum,
	// so an exact comparison would leave the end fade painted forever.
	const slack = 1
	const horizontal =
		props.orientation === "horizontal" || props.orientation === "both"
	const vertical = props.orientation !== "horizontal"

	const maxScrollLeft = viewport.scrollWidth - viewport.clientWidth
	// RTL viewports count scrollLeft down from 0 into the negatives, so 0 means the
	// right edge there — read the direction instead of assuming 0 is "at the start".
	const isRightToLeft = getComputedStyle(viewport).direction === "rtl"
	const distanceFromLeft = isRightToLeft
		? maxScrollLeft + viewport.scrollLeft
		: viewport.scrollLeft

	fadeLeft.value = horizontal && distanceFromLeft > slack
	fadeRight.value = horizontal && maxScrollLeft - distanceFromLeft > slack
	fadeTop.value = vertical && viewport.scrollTop > slack
	fadeBottom.value =
		vertical &&
		viewport.scrollHeight - viewport.clientHeight - viewport.scrollTop > slack
}

function edgeGradient(direction: string, fadeStart: boolean, fadeEnd: boolean) {
	const start = fadeStart ? `transparent 0, #000 ${props.fadeSize}` : "#000 0"
	const end = fadeEnd
		? `#000 calc(100% - ${props.fadeSize}), transparent 100%`
		: "#000 100%"
	return `linear-gradient(${direction}, ${start}, ${end})`
}

// Tailwind cannot express a mask whose stops depend on live scroll position, so this
// one visual is computed. A mask fades content to transparent rather than painting a
// gradient of some assumed page colour, which is what keeps it correct in dark mode.
const maskStyle = computed(() => {
	const layers: string[] = []
	if (fadeLeft.value || fadeRight.value) {
		layers.push(edgeGradient("to right", fadeLeft.value, fadeRight.value))
	}
	if (fadeTop.value || fadeBottom.value) {
		layers.push(edgeGradient("to bottom", fadeTop.value, fadeBottom.value))
	}
	if (!layers.length) {
		return undefined
	}

	const image = layers.join(", ")
	// Layers default to compositing as a union, which would cancel both fades out.
	return {
		maskImage: image,
		WebkitMaskImage: image,
		maskComposite: "intersect",
		WebkitMaskComposite: "source-in",
	}
})

let resizeObserver: ResizeObserver | undefined
let observedViewport: HTMLElement | null = null

onMounted(() => {
	const viewport = scrollAreaRef.value?.viewportElement
	if (!viewport) {
		return
	}

	observedViewport = viewport
	viewport.addEventListener("scroll", updateFades, { passive: true })
	// The viewport resizing changes what overflows; its inner wrapper resizing means
	// the content itself changed (rows loaded, filters applied).
	resizeObserver = new ResizeObserver(updateFades)
	resizeObserver.observe(viewport)
	if (viewport.firstElementChild) {
		resizeObserver.observe(viewport.firstElementChild)
	}
	updateFades()
})

onBeforeUnmount(() => {
	observedViewport?.removeEventListener("scroll", updateFades)
	resizeObserver?.disconnect()
})
</script>

<template>
	<ScrollArea
		ref="scrollAreaRef"
		:orientation="orientation"
		:scroll-hide-delay="scrollHideDelay"
		:viewport-class="viewportClass"
		:style="maskStyle"
	>
		<slot />
	</ScrollArea>
</template>
