<script setup lang="ts">
import type { ProductSize, ProductVariant } from "@/types"
import { FileUploader, createResource } from "frappe-ui"
import { computed, ref } from "vue"

const props = defineProps<{ variant: ProductVariant }>()
const emit = defineEmits<{ changed: [] }>()

const addImages = createResource({
	url: "ls_shop.api.admin.catalog.add_product_images",
	onSuccess: () => emit("changed"),
})

const removeImage = createResource({
	url: "ls_shop.api.admin.catalog.remove_product_image",
	onSuccess: () => emit("changed"),
})

const setPublished = createResource({
	url: "ls_shop.api.admin.catalog.set_variant_published",
	onSuccess: () => emit("changed"),
})

const savePrices = createResource({
	url: "ls_shop.api.admin.catalog.save_product_prices",
	onSuccess: () => emit("changed"),
})

const receiveStock = createResource({
	url: "ls_shop.api.admin.catalog.receive_product_stock",
	onSuccess: () => {
		receiveQuantities.value = {}
		emit("changed")
	},
})

const expanded = ref(false)
const rates = ref<Record<string, string>>({})
const receiveQuantities = ref<Record<string, string>>({})

const canPublish = computed(() => props.variant.blockers.length === 0)

function rateFor(size: ProductSize) {
	return rates.value[size.item_code] ?? size.rate ?? ""
}

function submitPrices() {
	savePrices.submit({
		style_attribute_variant: props.variant.name,
		size_prices: props.variant.sizes.map((size: ProductSize) => ({
			item_code: size.item_code,
			default_rate: rateFor(size),
		})),
	})
}

function submitStock() {
	receiveStock.submit({
		style_attribute_variant: props.variant.name,
		received_quantities: receiveQuantities.value,
	})
}
</script>

<template>
	<div class="rounded border border-outline-gray-2">
		<div class="flex items-center justify-between px-4 py-3">
			<button type="button" class="text-left" @click="expanded = !expanded">
				<div class="text-base text-ink-gray-8">{{ variant.option }}</div>
				<div class="text-p-sm text-ink-gray-5">
					{{ variant.sizes.length }} sizes · {{ variant.images.length }} images
				</div>
				<div v-if="variant.blockers.length" class="mt-1 text-p-sm text-ink-amber-3">
					{{ variant.blockers.join(" · ") }}
				</div>
			</button>

			<div class="flex items-center gap-3">
				<Badge
					:theme="variant.is_published ? 'green' : 'gray'"
					:label="variant.is_published ? 'Live' : 'Not live'"
				/>
				<Button
					:loading="setPublished.loading"
					:disabled="!variant.is_published && !canPublish"
					@click="
						setPublished.submit({
							style_attribute_variant: variant.name,
							publish: variant.is_published ? 0 : 1,
						})
					"
				>
					{{ variant.is_published ? "Unpublish" : "Publish" }}
				</Button>
			</div>
		</div>

		<div v-if="expanded" class="border-t border-outline-gray-2 px-4 py-4">
			<h3 class="mb-2 text-p-sm font-medium text-ink-gray-7">Images</h3>
			<div class="mb-4 flex flex-wrap items-center gap-2">
				<div v-for="image in variant.images" :key="image" class="group relative">
					<img :src="image" alt="" class="h-16 w-16 rounded object-cover" />
					<button
						type="button"
						class="absolute -right-1 -top-1 rounded-full bg-surface-gray-7 px-1.5 text-p-xs text-ink-white"
						@click="
							removeImage.submit({
								style_attribute_variant: variant.name,
								file_url: image,
							})
						"
					>
						×
					</button>
				</div>

				<FileUploader
					:file-types="['image/*']"
					@success="
						(file: { file_url: string }) =>
							addImages.submit({
								style_attribute_variant: variant.name,
								file_urls: [file.file_url],
							})
					"
				>
					<template #default="{ openFileSelector, uploading, progress }">
						<Button :loading="uploading" @click="openFileSelector">
							{{ uploading ? `Uploading ${progress}%` : "Add image" }}
						</Button>
					</template>
				</FileUploader>
			</div>

			<h3 class="mb-2 text-p-sm font-medium text-ink-gray-7">Sizes</h3>
			<table class="w-full text-base">
				<thead class="text-ink-gray-6">
					<tr>
						<th class="py-1 text-left font-medium">Size</th>
						<th class="py-1 text-left font-medium">Price</th>
						<th class="py-1 text-left font-medium">In stock</th>
						<th class="py-1 text-left font-medium">Receive</th>
					</tr>
				</thead>
				<tbody>
					<tr v-for="size in variant.sizes" :key="size.item_code">
						<td class="py-1 text-ink-gray-8">{{ size.size }}</td>
						<td class="py-1 pr-3">
							<input
								:value="rateFor(size)"
								type="number"
								class="w-24 rounded border border-outline-gray-2 px-2 py-1"
								@input="
									rates[size.item_code] = ($event.target as HTMLInputElement).value
								"
							/>
						</td>
						<td class="py-1 text-ink-gray-6">{{ size.stock }}</td>
						<td class="py-1">
							<input
								:value="receiveQuantities[size.item_code] ?? ''"
								type="number"
								class="w-20 rounded border border-outline-gray-2 px-2 py-1"
								@input="
									receiveQuantities[size.item_code] = (
										$event.target as HTMLInputElement
									).value
								"
							/>
						</td>
					</tr>
				</tbody>
			</table>

			<div class="mt-3 flex gap-2">
				<Button :loading="savePrices.loading" @click="submitPrices">Save prices</Button>
				<Button :loading="receiveStock.loading" @click="submitStock">Receive stock</Button>
			</div>

			<ErrorMessage
				class="mt-2"
				:message="
					savePrices.error?.messages?.[0] ||
					receiveStock.error?.messages?.[0] ||
					addImages.error?.messages?.[0] ||
					setPublished.error?.messages?.[0]
				"
			/>
		</div>
	</div>
</template>
