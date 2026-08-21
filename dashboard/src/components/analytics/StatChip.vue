<script setup lang="ts">
defineProps<{ label: string; value: string }>()
</script>

<!-- The headline trio each analytics widget prints above its own detail. -->
<template>
	<div class="rounded-4 border border-outline-gray-1 bg-surface-gray-1 px-3 py-2">
		<div class="truncate text-p-xs text-ink-gray-5">{{ label }}</div>
		<div class="mt-0.5 truncate text-base font-semibold text-ink-gray-8">
			{{ value }}
		</div>
		<slot />
	</div>
</template>
