<script setup lang="ts">
import CollectionCombobox from "@/components/CollectionCombobox.vue"
import OptionRow from "@/components/OptionRow.vue"
import type { ProductDetail, ProductVariant } from "@/types"
import { formatPriceRange, publishTheme, sumStock } from "@/utils/format"
import {
	Alert,
	Badge,
	Breadcrumbs,
	Button,
	FormControl,
	LoadingText,
	toast,
	useCall,
} from "frappe-ui"
import { computed, reactive, watch } from "vue"
import { useRoute } from "vue-router"

const route = useRoute()
const productName = computed(() => String(route.params.name))

const product = useCall<ProductDetail>({
	url: "/api/v2/method/ls_shop.api.admin.catalog.get_product",
	params: () => ({ item_template: productName.value }),
	refetch: true,
})

const details = reactive({ title: "", collection: "", description: "" })

watch(
	() => product.data,
	(data) => {
		if (!data) return
		details.title = data.title ?? ""
		details.collection = data.collection ?? ""
		details.description = data.description ?? ""
	},
	{ immediate: true },
)

const detailsChanged = computed(
	() =>
		!!product.data &&
		(details.title.trim() !== (product.data.title ?? "") ||
			details.collection !== (product.data.collection ?? "") ||
			details.description !== (product.data.description ?? "")),
)

const updateProduct = useCall({
	url: "/api/v2/method/ls_shop.api.admin.catalog.update_product",
	method: "POST",
	immediate: false,
	onSuccess: () => {
		toast.success("Product saved")
		product.reload()
	},
	onError: (error: Error) => toast.error(error.message),
})

const publishAll = useCall<{ updated: string[]; skipped: string[] }>({
	url: "/api/v2/method/ls_shop.api.admin.catalog.set_product_published",
	method: "POST",
	immediate: false,
	onSuccess: () => product.reload(),
	onError: (error: Error) => toast.error(error.message),
})

const variants = computed<ProductVariant[]>(() => product.data?.variants ?? [])
const liveCount = computed(
	() => variants.value.filter((variant) => variant.is_published).length,
)
const allLive = computed(
	() => variants.value.length > 0 && liveCount.value === variants.value.length,
)

const priceLabel = computed(() =>
	formatPriceRange(
		variants.value.flatMap((variant) => variant.sizes.map((size) => size.rate)),
	),
)
const stockTotal = computed(() =>
	variants.value.reduce((total, variant) => total + sumStock(variant.sizes), 0),
)

// The one thing an owner most needs to know is why the product is not selling yet, so lead with
// it rather than leaving them to notice a greyed-out switch.
const blockedOptions = computed(() =>
	variants.value
		.filter((variant) => variant.blockers.length > 0)
		.map((variant) => variant.option),
)

const storefrontUrl = computed(
	() =>
		variants.value.find(
			(variant) => variant.is_published && variant.storefront_url,
		)?.storefront_url ?? "",
)

const heroImage = computed(
	() =>
		product.data?.image ??
		variants.value.find((variant) => variant.images.length)?.images[0] ??
		"",
)

function saveDetails() {
	updateProduct.submit({
		item_template: productName.value,
		title: details.title,
		collection: details.collection,
		description: details.description,
	})
}
</script>

<template>
	<div class="flex h-full flex-col bg-surface-base">
		<header
			class="flex min-h-12 shrink-0 items-center justify-between border-b border-outline-gray-1 px-3 sm:px-5"
		>
			<Breadcrumbs
				:items="[
					{ label: 'Products', route: { name: 'Products' } },
					{ label: product.data?.title ?? 'Loading', route: '' },
				]"
			/>
			<div class="flex gap-2">
				<Button
					v-if="storefrontUrl"
					icon-left="lucide-external-link"
					label="View in store"
					:link="storefrontUrl"
				/>
				<Button
					v-if="variants.length"
					variant="solid"
					theme="gray"
					:loading="publishAll.loading"
					:label="allLive ? 'Unpublish all' : 'Publish all'"
					@click="
						publishAll.submit({ item_template: productName, publish: allLive ? 0 : 1 })
					"
				/>
			</div>
		</header>

		<LoadingText v-if="product.loading && !product.data" class="p-5" :lines="4" />

		<div v-else-if="product.data" class="flex min-h-0 flex-1 overflow-hidden">
			<!-- Main pane: the options are the work surface, so they get the width. -->
			<div class="min-w-0 flex-1 overflow-y-auto px-3 pb-40 pt-5 sm:px-5">
				<!-- Alert has no default slot and no orange theme in beta-37: body text passed as
				     children is dropped and an unknown theme leaves it unstyled and icon-less. -->
				<Alert
					v-if="blockedOptions.length"
					class="mb-5"
					theme="yellow"
					:dismissible="false"
					:title="`${blockedOptions.length} option${blockedOptions.length > 1 ? 's are' : ' is'} not ready to sell`"
					:description="`${blockedOptions.join(', ')} still needs a photo before it can go live.`"
				/>

				<div class="flex items-baseline justify-between">
					<h2 class="text-md text-ink-gray-9">Options</h2>
					<span class="text-sm text-ink-gray-5">{{ liveCount }} of {{ variants.length }} live</span>
				</div>

				<div class="mt-1 flex items-center gap-4 border-b border-outline-gray-1 pb-1.5">
					<span class="flex-1 text-sm text-ink-gray-5">Option</span>
					<span class="w-24 shrink-0 text-right text-sm text-ink-gray-5">Price</span>
					<span class="w-20 shrink-0 text-right text-sm text-ink-gray-5">Stock</span>
					<span class="w-16 shrink-0 text-right text-sm text-ink-gray-5">Live</span>
				</div>

				<div class="divide-y divide-outline-gray-1">
					<OptionRow
						v-for="variant in variants"
						:key="variant.name"
						:variant="variant"
						@changed="product.reload()"
					/>
				</div>
			</div>

			<!-- Side panel: what the product *is*, kept out of the way of what you came to change. -->
			<aside
				class="hidden w-80 shrink-0 flex-col overflow-y-auto border-l border-outline-gray-1 lg:flex"
			>
				<div class="flex items-center gap-3 border-b border-outline-gray-1 px-4 py-4">
					<img
						v-if="heroImage"
						:src="heroImage"
						alt=""
						class="size-12 shrink-0 rounded-lg object-cover"
					/>
					<div
						v-else
						class="grid size-12 shrink-0 place-items-center rounded-lg bg-surface-gray-2 text-ink-gray-4"
					>
						{{ details.title.slice(0, 1) }}
					</div>
					<div class="min-w-0">
						<div class="truncate text-base text-ink-gray-9">{{ product.data.title }}</div>
						<Badge
							class="mt-1"
							variant="subtle"
							:theme="publishTheme(liveCount)"
							:label="liveCount ? `${liveCount} live` : 'Not live'"
						/>
					</div>
				</div>

				<dl class="space-y-2.5 border-b border-outline-gray-1 px-4 py-4">
					<div class="flex items-center justify-between">
						<dt class="text-sm text-ink-gray-5">Options</dt>
						<dd class="text-base text-ink-gray-9">{{ variants.length }}</dd>
					</div>
					<div class="flex items-center justify-between">
						<dt class="text-sm text-ink-gray-5">Price</dt>
						<dd class="text-base text-ink-gray-9">{{ priceLabel }}</dd>
					</div>
					<div class="flex items-center justify-between">
						<dt class="text-sm text-ink-gray-5">In stock</dt>
						<dd class="text-base text-ink-gray-9">{{ stockTotal }}</dd>
					</div>
				</dl>

				<div class="space-y-4 px-4 py-4">
					<FormControl v-model="details.title" label="Title" required />
					<CollectionCombobox v-model="details.collection" />
					<FormControl
						v-model="details.description"
						type="textarea"
						label="Description"
						description="Shown on the product page."
						:rows="4"
					/>
					<Button
						class="w-full"
						:loading="updateProduct.loading"
						:disabled="!detailsChanged"
						:label="detailsChanged ? 'Save changes' : 'Saved'"
						@click="saveDetails"
					/>
				</div>
			</aside>
		</div>
	</div>
</template>
