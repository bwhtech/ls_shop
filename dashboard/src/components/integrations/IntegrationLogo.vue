<script setup lang="ts">
import { computed } from "vue"
import { getIntegrationLogo } from "./logos"

const props = defineProps<{ slug: string; label: string }>()

// The plate colour lives in the SVG rather than the markup so the template stays token-only.
const markup = computed(() => {
	const logo = getIntegrationLogo(props.slug, props.label)
	return `<svg viewBox="0 0 112 40" width="100%" height="100%" preserveAspectRatio="xMidYMid meet" role="img" aria-label="${props.label}" focusable="false"><rect width="112" height="40" rx="8" fill="${logo.background}" />${logo.svg}</svg>`
})
</script>

<template>
	<div class="h-9 w-24 shrink-0 overflow-hidden rounded-5 border border-outline-gray-2" v-html="markup" />
</template>
