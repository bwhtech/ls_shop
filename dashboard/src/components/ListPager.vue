<script setup lang="ts">
import { Button } from "frappe-ui"

defineProps<{
	loaded: number
	total: number
	noun: string
	hasMore: boolean
	loading: boolean
}>()

const emit = defineEmits<{ loadMore: [] }>()
</script>

<template>
	<div
		class="flex items-center gap-3 border-t border-outline-gray-1 px-3 py-2.5 sm:px-5"
	>
		<span class="text-sm text-ink-gray-5">
			Showing {{ loaded }} of {{ total }} {{ noun }}
		</span>
		<Button
			v-if="hasMore"
			class="ms-auto"
			:loading="loading"
			label="Load more"
			@click="emit('loadMore')"
		/>
	</div>
</template>
