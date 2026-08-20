<script setup lang="ts">
import { Button, FileUploader } from "frappe-ui"

const props = withDefaults(
	defineProps<{
		modelValue: string | null
		/** Show a thumbnail rather than the bare file name. */
		image?: boolean
		fileTypes?: string[]
	}>(),
	{ image: true, fileTypes: undefined },
)

const emit = defineEmits<{ "update:modelValue": [value: string | null] }>()

function fileName(url: string) {
	return url.split("/").pop() ?? url
}
</script>

<template>
	<div class="flex items-center justify-end gap-3">
		<a
			v-if="props.modelValue && props.image"
			:href="props.modelValue"
			target="_blank"
			rel="noopener"
			class="shrink-0"
		>
			<img
				:src="props.modelValue"
				alt=""
				class="size-9 rounded-4 border border-outline-gray-1 bg-surface-gray-1 object-contain"
			/>
		</a>
		<a
			v-else-if="props.modelValue"
			:href="props.modelValue"
			target="_blank"
			rel="noopener"
			class="max-w-40 truncate text-sm text-ink-blue-link"
		>
			{{ fileName(props.modelValue) }}
		</a>

		<FileUploader
			:file-types="props.fileTypes ?? (props.image ? ['image/*'] : undefined)"
			:upload-args="{ private: false }"
			@success="(file: { file_url: string }) => emit('update:modelValue', file.file_url)"
		>
			<template #default="{ openFileSelector, uploading }">
				<Button
					:loading="uploading"
					:label="props.modelValue ? 'Replace' : 'Upload'"
					@click="openFileSelector"
				/>
			</template>
		</FileUploader>

		<Button
			v-if="props.modelValue"
			icon="lucide-x"
			aria-label="Remove file"
			@click="emit('update:modelValue', null)"
		/>
	</div>
</template>
