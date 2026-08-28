<script setup lang="ts">
import { Button } from "frappe-ui"

defineProps<{ loading?: boolean; disabled?: boolean }>()

const emit = defineEmits<{ save: [] }>()
</script>

<!-- The one footer every settings tab ends on, so they cannot drift apart on spacing again. -->
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
