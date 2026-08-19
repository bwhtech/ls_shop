<script setup lang="ts">
import type { ProductSize, ProductVariant } from "@/types"
import { formatPriceRange, sumStock } from "@/utils/format"
import {
	Button,
	FileUploader,
	Switch,
	Tooltip,
	dialog,
	toast,
	useCall,
} from "frappe-ui"
import { computed, ref } from "vue"

const props = defineProps<{ variant: ProductVariant }>()
const emit = defineEmits<{ changed: [] }>()

const expanded = ref(false)
const rates = ref<Record<string, string>>({})
const receiveQuantities = ref<Record<string, string>>({})

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

const setPublished = useCall({
	url: "/api/v2/method/ls_shop.api.admin.catalog.set_variant_published",
	method: "POST",
	immediate: false,
	onSuccess: () => emit("changed"),
	onError: reportError,
})

const savePrices = useCall({
	url: "/api/v2/method/ls_shop.api.admin.catalog.save_product_prices",
	method: "POST",
	immediate: false,
	onSuccess: () => {
		toast.success("Prices saved")
		emit("changed")
	},
	onError: reportError,
})

const receiveStock = useCall({
	url: "/api/v2/method/ls_shop.api.admin.catalog.receive_product_stock",
	method: "POST",
	immediate: false,
	onSuccess: () => {
		toast.success("Stock received")
		receiveQuantities.value = {}
		emit("changed")
	},
	onError: reportError,
})

const canPublish = computed(() => props.variant.blockers.length === 0)
const blockerText = computed(() => props.variant.blockers.join(" · "))

const summary = computed(() => {
	const sizeCount = props.variant.sizes.length
	const prices = formatPriceRange(props.variant.sizes.map((size) => size.rate))
	return `${sizeCount} ${sizeCount === 1 ? "size" : "sizes"} · ${prices} · ${sumStock(props.variant.sizes)} in stock`
})

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
		size_prices: props.variant.sizes.map((size) => ({
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

function confirmRemoveImage(fileUrl: string) {
	dialog.confirm({
		title: "Remove this image?",
		message: "It will no longer appear on the storefront.",
		theme: "red",
		confirmLabel: "Remove",
		onConfirm: () =>
			removeImage.submit({
				style_attribute_variant: props.variant.name,
				file_url: fileUrl,
			}),
	})
}
</script>

<template>
	<div class="py-3">
		<div class="flex items-center gap-4">
			<button
				type="button"
				class="flex min-w-0 flex-1 items-center gap-3 text-left"
				@click="expanded = !expanded"
			>
				<img
					v-if="variant.images.length"
					:src="variant.images[0]"
					alt=""
					class="size-9 shrink-0 rounded object-cover"
				/>
				<div
					v-else
					class="grid size-9 shrink-0 place-items-center rounded bg-surface-gray-2 text-xs text-ink-gray-4"
				>
					{{ variant.option.slice(0, 1) }}
				</div>

				<div class="min-w-0">
					<div class="truncate text-base text-ink-gray-9">{{ variant.option }}</div>
					<div class="text-sm text-ink-gray-5">{{ summary }}</div>
					<div v-if="blockerText" class="text-p-xs text-ink-amber-6">{{ blockerText }}</div>
				</div>
			</button>

			<!-- Fixed-width slot so the switches line up in a column down the list. -->
			<div class="w-28 shrink-0">
				<Tooltip :text="blockerText" :disabled="canPublish">
					<div class="flex justify-end">
						<Switch
							v-model="isLive"
							label="Live"
							:disabled="!variant.is_published && !canPublish"
						/>
					</div>
				</Tooltip>
			</div>
		</div>

		<div v-if="expanded" class="mt-4 space-y-5 pl-12">
			<div>
				<h3 class="text-sm text-ink-gray-5">Images</h3>
				<div class="mt-2 flex flex-wrap items-center gap-2">
					<div v-for="image in variant.images" :key="image" class="group relative">
						<img :src="image" alt="" class="size-16 rounded object-cover" />
						<button
							type="button"
							class="absolute -right-1.5 -top-1.5 hidden size-5 place-items-center rounded-full bg-surface-gray-7 text-2xs text-ink-white group-hover:grid"
							aria-label="Remove image"
							@click="confirmRemoveImage(image)"
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
							<Button
								icon-left="lucide-image-plus"
								:loading="uploading"
								:label="uploading ? `Uploading ${progress}%` : 'Add image'"
								@click="openFileSelector"
							/>
						</template>
					</FileUploader>
				</div>
			</div>

			<div>
				<h3 class="text-sm text-ink-gray-5">Sizes</h3>
				<table class="mt-2 w-full max-w-lg">
					<thead>
						<tr class="text-sm text-ink-gray-5">
							<th class="pb-1 text-left font-normal">Size</th>
							<th class="pb-1 text-left font-normal">Price</th>
							<th class="pb-1 text-right font-normal">In stock</th>
							<th class="pb-1 text-right font-normal">Receive</th>
						</tr>
					</thead>
					<tbody class="divide-y divide-outline-gray-1">
						<tr v-for="size in variant.sizes" :key="size.item_code">
							<td class="py-1.5 text-base text-ink-gray-9">{{ size.size }}</td>
							<td class="py-1.5">
								<input
									:value="rateFor(size)"
									type="number"
									class="w-24 rounded border border-outline-gray-2 bg-surface-base px-2 py-1 text-base text-ink-gray-9"
									@input="
										rates[size.item_code] = ($event.target as HTMLInputElement).value
									"
								/>
							</td>
							<td class="py-1.5 text-right text-base text-ink-gray-7">{{ size.stock }}</td>
							<td class="py-1.5 text-right">
								<input
									:value="receiveQuantities[size.item_code] ?? ''"
									type="number"
									placeholder="0"
									class="w-20 rounded border border-outline-gray-2 bg-surface-base px-2 py-1 text-right text-base text-ink-gray-9"
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
					<Button
						:loading="receiveStock.loading"
						icon-left="lucide-package-plus"
						label="Receive stock"
						@click="submitStock"
					/>
				</div>
			</div>
		</div>
	</div>
</template>
