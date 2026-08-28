<script setup lang="ts">
import { Button } from "frappe-ui"

withDefaults(defineProps<{ title?: string; message?: string }>(), {
	title: "Could not load this",
	message: "",
})

const emit = defineEmits<{ retry: [] }>()
</script>

<!--
	What a screen shows when its request came back with an error.

	`useCall` nulls `data` on a failed response, so a screen that only branches on loading and data
	renders its empty state - or nothing at all - for a request that actually failed.
-->
<template>
	<div class="flex flex-col items-center gap-1 px-5 py-16 text-center">
		<span class="text-sm-medium text-ink-red-7">{{ title }}</span>
		<span v-if="message" class="max-w-sm text-p-sm text-ink-gray-5">
			{{ message }}
		</span>
		<Button class="mt-3" label="Try again" @click="emit('retry')" />
	</div>
</template>
