<script setup lang="ts">
import VariantRow from "@/components/VariantRow.vue"
import type { ProductDetail, ProductVariant } from "@/types"
import { formatPriceRange, publishTheme, sumStock } from "@/utils/format"
import {
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

// Options that were skipped are the ones still missing an image or a size; naming them beats a
// silent partial success the owner has to go hunting for.
const skippedNotice = computed(() => {
	const skipped = publishAll.data?.skipped ?? []
	return skipped.length
		? `Still not live: ${skipped.join(", ")} — add an image first.`
		: ""
})

// Only a live option has a page a customer can actually open.
const storefrontUrl = computed(
	() =>
		variants.value.find(
			(variant) => variant.is_published && variant.storefront_url,
		)?.storefront_url ?? "",
)

const collectionOptions = computed(() => collections.data ?? [])

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
			class="flex min-h-12 items-center justify-between border-b border-outline-gray-1 px-3 sm:px-5"
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

		<div class="min-h-0 flex-1 overflow-y-auto">
			<div class="body-container pb-40 pt-5">
				<LoadingText v-if="product.loading && !product.data" :lines="3" />

				<template v-else-if="product.data">
					<dl class="flex gap-8 pb-5">
						<div>
							<dt class="text-sm text-ink-gray-5">Storefront</dt>
							<dd class="mt-1">
								<Badge
									variant="subtle"
									:theme="publishTheme(liveCount)"
									:label="liveCount ? `${liveCount} live` : 'Not live'"
								/>
							</dd>
						</div>
						<div>
							<dt class="text-sm text-ink-gray-5">Price</dt>
							<dd class="mt-1 text-base text-ink-gray-9">{{ priceLabel }}</dd>
						</div>
						<div>
							<dt class="text-sm text-ink-gray-5">In stock</dt>
							<dd class="mt-1 text-base text-ink-gray-9">{{ stockTotal }}</dd>
						</div>
					</dl>

					<section>
						<div class="flex items-baseline gap-2">
							<h2 class="text-md text-ink-gray-9">Options</h2>
							<span class="text-sm text-ink-gray-5">
								{{ liveCount }} of {{ variants.length }} live
							</span>
						</div>

						<p v-if="skippedNotice" class="mt-1 text-p-sm text-ink-amber-6">
							{{ skippedNotice }}
						</p>

						<div class="mt-2 divide-y divide-outline-gray-1 border-y border-outline-gray-1">
							<VariantRow
								v-for="variant in variants"
								:key="variant.name"
								:variant="variant"
								@changed="product.reload()"
							/>
						</div>
					</section>

					<section class="mt-6">
						<h2 class="text-md text-ink-gray-9">Details</h2>
						<div class="mt-3 max-w-xl space-y-4">
							<FormControl v-model="details.title" label="Title" required />
							<FormControl
								v-model="details.collection"
								type="select"
								label="Collection"
								:options="collectionOptions"
							/>
							<FormControl
								v-model="details.description"
								type="textarea"
								label="Description"
								description="Shown to customers on the product page."
								:rows="4"
							/>
							<div class="flex justify-end">
								<Button
									:loading="updateProduct.loading"
									:disabled="!detailsChanged"
									label="Save changes"
									@click="saveDetails"
								/>
							</div>
						</div>
					</section>
				</template>
			</div>
		</div>
	</div>
</template>
