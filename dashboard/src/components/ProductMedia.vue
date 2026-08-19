<script setup lang="ts">
import type { ProductVariant } from "@/types"
import { Button, FileUploader, dialog, toast, useCall } from "frappe-ui"

defineProps<{ variants: ProductVariant[] }>()
const emit = defineEmits<{ changed: [] }>()

function reportError(error: Error) {
	toast.error(error.message)
}

const addImages = useCall({
	url: "/api/v2/method/ls_shop.api.admin.catalog.add_product_images",
	method: "POST",
	immediate: false,
	onSuccess: () => emit("changed"),
	onError: reportError,
})

const removeImage = useCall({
	url: "/api/v2/method/ls_shop.api.admin.catalog.remove_product_image",
	method: "POST",
	immediate: false,
	onSuccess: () => emit("changed"),
	onError: reportError,
})

function confirmRemove(variantName: string, fileUrl: string) {
	dialog.confirm({
		title: "Remove this photo?",
		message: "It will no longer appear on the storefront.",
		theme: "red",
		confirmLabel: "Remove",
		onConfirm: () =>
			removeImage.submit({
				style_attribute_variant: variantName,
				file_url: fileUrl,
			}),
	})
}
</script>

<template>
	<!-- Photos belong to an option, not to the product, so they stay grouped by option rather
	     than pooled into one gallery that silently drops which colour it belongs to. -->
	<div class="divide-y divide-outline-gray-1">
		<div v-for="variant in variants" :key="variant.name" class="flex gap-4 px-4 py-3.5">
			<div class="w-24 shrink-0 pt-1">
				<div class="truncate text-base text-ink-gray-9">{{ variant.option }}</div>
				<div v-if="!variant.images.length" class="text-xs text-ink-amber-6">Needs a photo</div>
			</div>

			<div class="flex flex-wrap items-center gap-2">
				<div v-for="image in variant.images" :key="image" class="group relative">
					<img
						:src="image"
						alt=""
						class="size-20 rounded-md border border-outline-gray-1 object-cover"
					/>
					<button
						type="button"
						class="absolute -right-1.5 -top-1.5 hidden size-5 place-items-center rounded-full bg-surface-gray-7 text-ink-white group-hover:grid"
						aria-label="Remove photo"
						@click="confirmRemove(variant.name, image)"
					>
						<span class="lucide-x size-3" aria-hidden="true" />
					</button>
				</div>

				<FileUploader
					:file-types="['image/*']"
					:upload-args="{ private: false }"
					@success="
						(file: { file_url: string }) =>
							addImages.submit({
								style_attribute_variant: variant.name,
								file_urls: [file.file_url],
							})
					"
				>
					<template #default="{ openFileSelector, uploading, progress }">
						<button
							type="button"
							class="grid size-20 place-items-center rounded-md border border-dashed border-outline-gray-2 text-ink-gray-5 hover:bg-surface-gray-1"
							:aria-label="`Add a photo to ${variant.option}`"
							@click="openFileSelector"
						>
							<span v-if="uploading" class="text-xs">{{ progress }}%</span>
							<span v-else class="lucide-plus size-5" aria-hidden="true" />
						</button>
					</template>
				</FileUploader>
			</div>
		</div>
	</div>
</template>
