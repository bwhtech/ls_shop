<script setup lang="ts">
import OptionsTable from "@/components/OptionsTable.vue"
import ProductMedia from "@/components/ProductMedia.vue"
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

const collections = useCall<string[]>({
	url: "/api/v2/method/ls_shop.api.admin.catalog.get_collections",
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

		<template v-else-if="product.data">
			<!-- Identity strip: what this product is and whether it is selling, before any form. -->
			<div
				class="flex shrink-0 items-center gap-4 border-b border-outline-gray-1 px-3 py-4 sm:px-5"
			>
				<img
					v-if="heroImage"
					:src="heroImage"
					alt=""
					class="size-14 shrink-0 rounded-lg object-cover"
				/>
				<div
					v-else
					class="grid size-14 shrink-0 place-items-center rounded-lg bg-surface-gray-2 text-ink-gray-4"
				>
					{{ details.title.slice(0, 1) }}
				</div>

				<div class="min-w-0">
					<h1 class="truncate text-lg text-ink-gray-9">{{ product.data.title }}</h1>
					<div class="mt-1 flex items-center gap-2">
						<Badge
							variant="subtle"
							:theme="publishTheme(liveCount)"
							:label="liveCount ? `${liveCount} of ${variants.length} live` : 'Not live'"
						/>
						<span class="text-sm text-ink-gray-5">
							{{ priceLabel }} · {{ stockTotal }} in stock
						</span>
					</div>
				</div>
			</div>

			<div class="flex min-h-0 flex-1 overflow-hidden">
				<div class="min-w-0 flex-1 overflow-y-auto px-3 pb-40 pt-5 sm:px-5">
					<Alert
						v-if="blockedOptions.length"
						class="mb-5"
						theme="orange"
						:title="`${blockedOptions.length} option${blockedOptions.length > 1 ? 's are' : ' is'} not ready to sell`"
					>
						{{ blockedOptions.join(", ") }} still needs a photo before it can go live.
					</Alert>

					<section class="mb-5 rounded-lg border border-outline-gray-1">
						<h2 class="border-b border-outline-gray-1 px-4 py-3 text-base text-ink-gray-9">
							Details
						</h2>
						<div class="space-y-4 p-4">
							<FormControl v-model="details.title" label="Title" required />
							<FormControl
								v-model="details.collection"
								type="select"
								label="Collection"
								:options="collections.data ?? []"
							/>
							<FormControl
								v-model="details.description"
								type="textarea"
								label="Description"
								description="Shown to customers on the product page."
								:rows="3"
							/>
							<div class="flex justify-end">
								<Button
									:loading="updateProduct.loading"
									:disabled="!detailsChanged"
									:label="detailsChanged ? 'Save changes' : 'Saved'"
									@click="saveDetails"
								/>
							</div>
						</div>
					</section>

					<section class="mb-5 rounded-lg border border-outline-gray-1">
						<h2 class="border-b border-outline-gray-1 px-4 py-3 text-base text-ink-gray-9">
							Photos
						</h2>
						<ProductMedia :variants="variants" @changed="product.reload()" />
					</section>

					<section class="rounded-lg border border-outline-gray-1">
						<h2 class="border-b border-outline-gray-1 px-4 py-3 text-base text-ink-gray-9">
							Options &amp; inventory
						</h2>
						<OptionsTable :variants="variants" @changed="product.reload()" />
					</section>
				</div>
			</div>
		</template>
	</div>
</template>
