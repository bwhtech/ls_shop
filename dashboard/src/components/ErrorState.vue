<script setup lang="ts">
import { Button } from "frappe-ui"

withDefaults(defineProps<{ title?: string; message?: string }>(), {
	title: "Could not load this",
	message: "",
})

const emit = defineEmits<{ retry: [] }>()
</script>

<!-- `useCall` nulls `data` on a failed response, so a screen branching only on loading and data would render its empty state. -->
<template>
	<div class="flex flex-col items-center gap-1 px-5 py-16 text-center">
		<span class="text-sm-medium text-ink-red-7">{{ title }}</span>
		<span v-if="message" class="max-w-sm break-words text-p-sm text-ink-gray-5">
			{{ message }}
		</span>
		<Button class="mt-3" label="Try again" @click="emit('retry')" />
	</div>
</template>
