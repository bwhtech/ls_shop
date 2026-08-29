<script setup lang="ts">
import { Button } from "frappe-ui"

defineProps<{ loading?: boolean; disabled?: boolean }>()

const emit = defineEmits<{ save: [] }>()
</script>

<template>
	<div class="flex justify-end pt-4">
		<Button
			variant="solid"
			theme="gray"
			label="Save"
			:loading="loading"
			:disabled="disabled"
			@click="emit('save')"
		/>
	</div>
</template>
