<script setup lang="ts">
import { Button } from "frappe-ui"

defineProps<{
	loaded: number
	total: number
	/** Plural noun for what the list holds, e.g. "orders". */
	noun: string
	hasMore: boolean
	loading: boolean
}>()

const emit = defineEmits<{ loadMore: [] }>()
</script>

<!--
	The count under a list, and the way to see the rest of it.

	The endpoints answer one page at a time, so a bare total above a list reads as a promise the
	rows do not keep - "412 sizes" over 50 rows. This says how much of the total is on screen.
-->
<template>
	<div
		class="flex items-center gap-3 border-t border-outline-gray-1 px-3 py-2.5 sm:px-5"
	>
		<span class="text-sm text-ink-gray-5">
			Showing {{ loaded }} of {{ total }} {{ noun }}
		</span>
		<Button
			v-if="hasMore"
			class="ml-auto"
			:loading="loading"
			label="Load more"
			@click="emit('loadMore')"
		/>
	</div>
</template>
