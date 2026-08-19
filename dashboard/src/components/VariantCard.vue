<script setup lang="ts">
import type { ProductSize, ProductVariant } from "@/types"
import {
	Button,
	FileUploader,
	Switch,
	Tooltip,
	createResource,
	toast,
} from "frappe-ui"
import { computed, ref } from "vue"

const props = defineProps<{ variant: ProductVariant }>()
const emit = defineEmits<{ changed: [] }>()

function reportError(error: { messages?: string[]; message?: string } | null) {
	toast.error(
		error?.messages?.length
			? error.messages.join(", ")
			: (error?.message ?? "Failed"),
	)
}

const addImages = createResource({
	url: "ls_shop.api.admin.catalog.add_product_images",
	onSuccess: () => emit("changed"),
	onError: reportError,
})

const removeImage = createResource({
	url: "ls_shop.api.admin.catalog.remove_product_image",
	onSuccess: () => emit("changed"),
	onError: reportError,
})

const setPublished = createResource({
	url: "ls_shop.api.admin.catalog.set_variant_published",
	onSuccess: () => emit("changed"),
	onError: reportError,
})

const savePrices = createResource({
	url: "ls_shop.api.admin.catalog.save_product_prices",
	onSuccess: () => {
		toast.success("Prices saved")
		emit("changed")
	},
	onError: reportError,
})

const receiveStock = createResource({
	url: "ls_shop.api.admin.catalog.receive_product_stock",
	onSuccess: () => {
		toast.success("Stock received")
		receiveQuantities.value = {}
		emit("changed")
	},
	onError: reportError,
})

const expanded = ref(false)
const rates = ref<Record<string, string>>({})
const receiveQuantities = ref<Record<string, string>>({})

const canPublish = computed(() => props.variant.blockers.length === 0)
const publishHint = computed(() =>
	canPublish.value ? "" : props.variant.blockers.join(" · "),
)
const isLive = computed({
	get: () => props.variant.is_published,
	set: (value: boolean) =>
		setPublished.submit({
			style_attribute_variant: props.variant.name,
			publish: value ? 1 : 0,
		}),
})

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
	<div class="rounded-lg border border-outline-gray-2 bg-surface-white">
		<div class="flex items-center gap-4 px-4 py-3">
			<button
				type="button"
				class="flex min-w-0 flex-1 items-center gap-3 text-left"
				@click="expanded = !expanded"
			>
				<img
					v-if="variant.images.length"
					:src="variant.images[0]"
					alt=""
					class="size-10 shrink-0 rounded object-cover"
				/>
				<div
					v-else
					class="grid size-10 shrink-0 place-items-center rounded bg-surface-gray-2 text-p-xs text-ink-gray-5"
				>
					—
				</div>

				<div class="min-w-0">
					<div class="truncate text-base font-medium text-ink-gray-8">
						{{ variant.option }}
					</div>
					<div class="text-p-sm text-ink-gray-5">
						{{ variant.sizes.length }} sizes · {{ variant.images.length }} images
					</div>
					<div v-if="publishHint" class="mt-0.5 text-p-sm text-ink-amber-3">
						{{ publishHint }}
					</div>
				</div>
			</button>

			<Tooltip :text="publishHint" :disabled="canPublish">
				<div>
					<Switch
						v-model="isLive"
						label="Live"
						:disabled="!variant.is_published && !canPublish"
					/>
				</div>
			</Tooltip>
		</div>

		<div v-if="expanded" class="border-t border-outline-gray-2 px-4 py-4">
			<h3 class="mb-2 text-p-sm font-medium text-ink-gray-7">Images</h3>
			<div class="mb-5 flex flex-wrap items-center gap-2">
				<div v-for="image in variant.images" :key="image" class="group relative">
					<img :src="image" alt="" class="size-16 rounded object-cover" />
					<button
						type="button"
						class="absolute -right-1.5 -top-1.5 hidden size-5 place-items-center rounded-full bg-surface-gray-7 text-p-xs text-ink-white group-hover:grid"
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
						<Button
							:loading="uploading"
							:label="uploading ? `Uploading ${progress}%` : 'Add image'"
							@click="openFileSelector"
						/>
					</template>
				</FileUploader>
			</div>

			<h3 class="mb-2 text-p-sm font-medium text-ink-gray-7">Sizes</h3>
			<table class="w-full text-base">
				<thead>
					<tr class="text-p-sm text-ink-gray-5">
						<th class="pb-1 text-left font-normal">Size</th>
						<th class="pb-1 text-left font-normal">Price</th>
						<th class="pb-1 text-left font-normal">In stock</th>
						<th class="pb-1 text-left font-normal">Receive</th>
					</tr>
				</thead>
				<tbody>
					<tr v-for="size in variant.sizes" :key="size.item_code">
						<td class="py-1 text-ink-gray-8">{{ size.size }}</td>
						<td class="py-1 pr-3">
							<input
								:value="rateFor(size)"
								type="number"
								class="w-24 rounded border border-outline-gray-2 bg-surface-gray-2 px-2 py-1 text-ink-gray-8"
								@input="rates[size.item_code] = ($event.target as HTMLInputElement).value"
							/>
						</td>
						<td class="py-1 text-ink-gray-6">{{ size.stock }}</td>
						<td class="py-1">
							<input
								:value="receiveQuantities[size.item_code] ?? ''"
								type="number"
								placeholder="0"
								class="w-20 rounded border border-outline-gray-2 bg-surface-gray-2 px-2 py-1 text-ink-gray-8"
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
				<Button :loading="savePrices.loading" label="Save prices" @click="submitPrices" />
				<Button :loading="receiveStock.loading" label="Receive stock" @click="submitStock" />
			</div>
		</div>
	</div>
</template>
