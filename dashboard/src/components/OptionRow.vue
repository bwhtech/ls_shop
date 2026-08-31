<script setup lang="ts">
import type { ProductSize, ProductVariant, UploadedFile } from "@/types"
import { errorMessage } from "@/utils/errors"
import { formatPriceRange, sumStock } from "@/utils/format"
import {
	Button,
	FileUploader,
	Switch,
	TextInput,
	Tooltip,
	dialog,
	toast,
	useCall,
} from "frappe-ui"
import {
	List,
	ListCell,
	ListHeader,
	ListHeaderCell,
	ListRow,
	ListRows,
} from "frappe-ui/list"
import { computed, ref, watch } from "vue"

const props = defineProps<{ variant: ProductVariant }>()
const emit = defineEmits<{ changed: [] }>()

const expanded = ref(false)
const rates = ref<Record<string, string>>({})
const receiveQuantities = ref<Record<string, string>>({})

function reportError(error: Error) {
	toast.error(errorMessage(error))
}

function call<TParams extends Record<string, unknown>>(
	method: string,
	onSuccess?: () => void,
) {
	return useCall<unknown, TParams>({
		url: `/api/v2/method/ls_shop.api.admin.catalog.${method}`,
		method: "POST",
		immediate: false,
		onSuccess: () => {
			onSuccess?.()
			emit("changed")
		},
		onError: reportError,
	})
}

const addImages = call<{
	style_attribute_variant: string
	file_urls: string[]
}>("add_product_images")
const removeImage = call<{ style_attribute_variant: string; file_url: string }>(
	"remove_product_image",
)
const setPublished = call<{ style_attribute_variant: string; publish: number }>(
	"set_variant_published",
)
const savePrices = call<{
	style_attribute_variant: string
	size_prices: { item_code: string; default_rate: string }[]
}>("save_product_prices", () => toast.success("Prices saved"))
const receiveStock = call<{
	style_attribute_variant: string
	received_quantities: Record<string, string>
}>("receive_product_stock", () => {
	toast.success("Stock received")
	receiveQuantities.value = {}
})

const canPublish = computed(() => props.variant.blockers.length === 0)
const blockerText = computed(() => props.variant.blockers.join(" · "))
const priceLabel = computed(() =>
	formatPriceRange(props.variant.sizes.map((size) => size.rate)),
)
const stockTotal = computed(() => sumStock(props.variant.sizes))

const isLive = ref(props.variant.is_published)
const publishing = ref(false)

watch(
	() => props.variant.is_published,
	(published) => {
		isLive.value = published
	},
)

async function setLive(published: boolean) {
	isLive.value = published
	publishing.value = true
	try {
		await setPublished.submit({
			style_attribute_variant: props.variant.name,
			publish: published ? 1 : 0,
		})
		if (setPublished.error) isLive.value = props.variant.is_published
	} finally {
		publishing.value = false
	}
}

const pendingReceipt = computed(() =>
	Object.fromEntries(
		Object.entries(receiveQuantities.value).filter(
			([, quantity]) => Number(quantity) > 0,
		),
	),
)
const hasPendingReceipt = computed(
	() => Object.keys(pendingReceipt.value).length > 0,
)

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

function addImage(file: UploadedFile) {
	addImages.submit({
		style_attribute_variant: props.variant.name,
		file_urls: [file.file_url],
	})
}

function confirmRemoveImage(fileUrl: string) {
	dialog.confirm({
		title: "Remove this image?",
		message: "It will no longer appear on the storefront.",
		theme: "red",
		confirmLabel: "Remove",
		onConfirm: async () => {
			await removeImage.submit({
				style_attribute_variant: props.variant.name,
				file_url: fileUrl,
			})
		},
	})
}
</script>

<template>
	<div>
		<div class="flex items-center gap-4 py-2.5">
			<button
				type="button"
				class="flex min-w-0 flex-1 items-center gap-3 text-start"
				:aria-expanded="expanded"
				@click="expanded = !expanded"
			>
				<span
					class="size-4 shrink-0 text-ink-gray-4 transition-transform"
					:class="expanded ? 'lucide-chevron-down' : 'lucide-chevron-right'"
					aria-hidden="true"
				/>
				<img
					v-if="variant.images.length"
					:src="variant.images[0]"
					alt=""
					class="size-9 shrink-0 rounded-4 object-cover"
				/>
				<div
					v-else
					class="grid size-9 shrink-0 place-items-center rounded-4 bg-surface-gray-2 text-xs text-ink-gray-4"
				>
					{{ variant.option.slice(0, 1) }}
				</div>

				<div class="min-w-0">
					<div class="truncate text-base text-ink-gray-9">{{ variant.option }}</div>
					<div class="text-sm text-ink-gray-5">
						{{ variant.sizes.length }} {{ variant.sizes.length === 1 ? "size" : "sizes" }}
						<span v-if="blockerText" class="text-ink-amber-6">· {{ blockerText }}</span>
					</div>
				</div>
			</button>

			<div class="w-24 shrink-0 text-end text-base text-ink-gray-7">{{ priceLabel }}</div>
			<div class="w-20 shrink-0 text-end text-base text-ink-gray-7">{{ stockTotal }}</div>
			<div class="w-16 shrink-0">
				<Tooltip :text="blockerText" :disabled="canPublish">
					<div class="flex justify-end">
						<Switch
							:model-value="isLive"
							:disabled="publishing || (!variant.is_published && !canPublish)"
							@update:model-value="setLive"
						/>
					</div>
				</Tooltip>
			</div>
		</div>

		<div v-if="expanded" class="space-y-5 pb-5 ps-12 pe-4">
			<div>
				<h4 class="text-sm text-ink-gray-5">Photos</h4>
				<div class="mt-2 flex flex-wrap items-center gap-2">
					<div v-for="image in variant.images" :key="image" class="group relative">
						<img
							:src="image"
							alt=""
							class="size-20 rounded-4 border border-outline-gray-1 object-cover"
						/>
						<Button
							class="absolute -end-1.5 -top-1.5 hidden rounded-full group-hover:inline-flex"
							variant="subtle"
							size="xs"
							icon="lucide-x"
							aria-label="Remove photo"
							@click="confirmRemoveImage(image)"
						/>
					</div>

					<FileUploader
						:file-types="['image/*']"
						:upload-args="{ private: false }"
						@success="addImage"
					>
						<template #default="{ openFileSelector, uploading, progress }">
							<button
								type="button"
								class="grid size-20 place-items-center rounded-4 border border-dashed border-outline-gray-2 text-ink-gray-5 hover:bg-surface-gray-1"
								@click="openFileSelector"
							>
								<span v-if="uploading" class="text-xs">{{ progress }}%</span>
								<span v-else class="lucide-plus size-5" aria-hidden="true" />
							</button>
						</template>
					</FileUploader>
				</div>
			</div>

			<div>
				<h4 class="text-sm text-ink-gray-5">Sizes</h4>
				<List
					class="mt-2 max-w-md"
					:columns="['minmax(0,1fr)', '7rem', '5rem', '6rem']"
				>
					<ListHeader>
						<ListHeaderCell>Size</ListHeaderCell>
						<ListHeaderCell class="justify-end">Price</ListHeaderCell>
						<ListHeaderCell class="justify-end">In stock</ListHeaderCell>
						<ListHeaderCell class="justify-end">Add stock</ListHeaderCell>
					</ListHeader>
					<ListRows :items="variant.sizes" row-key="item_code" v-slot="{ item: size }">
						<ListRow class="py-2">
							<ListCell>
								<span class="truncate text-base text-ink-gray-9">{{ size.size }}</span>
							</ListCell>
							<ListCell class="justify-end">
								<!-- The browser's own text-align on <input> beats the wrapper's, so it has to reach the control slot. -->
								<TextInput
									class="w-24 [&_[data-slot=control]]:text-end"
									type="number"
									:aria-label="`Price for size ${size.size}`"
									:model-value="rateFor(size)"
									@update:model-value="rates[size.item_code] = $event"
								/>
							</ListCell>
							<ListCell class="justify-end">
								<span class="text-base text-ink-gray-7">{{ size.stock }}</span>
							</ListCell>
							<ListCell class="justify-end">
								<TextInput
									class="w-20 [&_[data-slot=control]]:text-end"
									type="number"
									placeholder="0"
									:aria-label="`Add stock for size ${size.size}`"
									:model-value="receiveQuantities[size.item_code] ?? ''"
									@update:model-value="receiveQuantities[size.item_code] = $event"
								/>
							</ListCell>
						</ListRow>
					</ListRows>
				</List>

				<div class="mt-3 flex gap-2">
					<Button :loading="savePrices.loading" label="Save prices" @click="submitPrices" />
					<Button
						:loading="receiveStock.loading"
						:disabled="!hasPendingReceipt"
						icon-left="lucide-package-plus"
						label="Add stock"
						@click="
							receiveStock.submit({
								style_attribute_variant: variant.name,
								received_quantities: pendingReceipt,
							})
						"
					/>
				</div>
			</div>
		</div>
	</div>
</template>
