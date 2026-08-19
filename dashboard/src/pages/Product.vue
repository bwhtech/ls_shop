<script setup lang="ts">
import VariantCard from "@/components/VariantCard.vue"
import type { ProductVariant } from "@/types"
import {
	Badge,
	Breadcrumbs,
	PageHeader,
	Skeleton,
	createResource,
} from "frappe-ui"
import { computed, ref, watch } from "vue"
import { useRoute } from "vue-router"

const route = useRoute()
const productName = computed(() => String(route.params.name))

const product = createResource({
	url: "ls_shop.api.admin.catalog.get_product",
	makeParams: () => ({ item_template: productName.value }),
	auto: true,
})

const title = ref("")
watch(
	() => product.data?.title,
	(value) => {
		title.value = value ?? ""
	},
)

const updateProduct = createResource({
	url: "ls_shop.api.admin.catalog.update_product",
	onSuccess: () => product.reload(),
})

const publishAll = createResource({
	url: "ls_shop.api.admin.catalog.set_product_published",
	onSuccess: () => product.reload(),
})

// Options that were skipped are the ones still missing an image or a size; naming them beats a
// silent partial success the owner has to go hunting for.
const skippedNotice = computed(() => {
	const skipped = publishAll.data?.skipped ?? []
	return skipped.length
		? `Still not live: ${skipped.join(", ")} — add an image first.`
		: ""
})

const variants = computed<ProductVariant[]>(() => product.data?.variants ?? [])
const allLive = computed(
	() =>
		variants.value.length > 0 &&
		variants.value.every((variant) => variant.is_published),
)
const liveCount = computed(
	() => variants.value.filter((variant) => variant.is_published).length,
)
const titleChanged = computed(
	() => title.value.trim() !== (product.data?.title ?? ""),
)

const allRates = computed(() =>
	variants.value
		.flatMap((variant) => variant.sizes.map((size) => size.rate))
		.filter((rate): rate is number => rate !== null && rate !== undefined),
)

const priceLabel = computed(() => {
	if (!allRates.value.length) return "No price"
	const low = Math.min(...allRates.value)
	const high = Math.max(...allRates.value)
	return low === high ? String(low) : `${low} – ${high}`
})

const stockTotal = computed(() =>
	variants.value.reduce(
		(total, variant) =>
			total + variant.sizes.reduce((sum, size) => sum + (size.stock ?? 0), 0),
		0,
	),
)

// The storefront route only exists for options that are live, so link the first one that is.
const storefrontRoute = computed(
	() =>
		variants.value.find((variant) => variant.is_published && variant.route)
			?.route ?? "",
)
</script>

<template>
	<PageHeader>
		<Breadcrumbs
			:items="[
				{ label: 'Products', route: { name: 'Products' } },
				{ label: product.data?.title ?? '…', route: '' },
			]"
		/>
		<Button
			v-if="variants.length"
			variant="solid"
			:loading="publishAll.loading"
			:label="allLive ? 'Unpublish all' : 'Publish all'"
			@click="publishAll.submit({ item_template: productName, publish: allLive ? 0 : 1 })"
		/>
	</PageHeader>

	<div class="h-full overflow-y-auto">
		<div class="mx-auto max-w-5xl px-5 py-5">
			<div v-if="product.loading && !product.data" class="space-y-3">
				<Skeleton class="h-24 w-full" />
				<Skeleton class="h-20 w-full" />
			</div>

			<div v-else-if="product.data" class="flex flex-col gap-5 lg:flex-row">
				<div class="min-w-0 flex-1 space-y-5">
					<section class="rounded-lg border border-outline-gray-2 p-4">
						<h2 class="mb-3 text-base font-medium text-ink-gray-8">Details</h2>
						<div class="flex items-end gap-2">
							<FormControl v-model="title" label="Title" class="flex-1" />
							<Button
								:loading="updateProduct.loading"
								:disabled="!titleChanged"
								label="Save"
								@click="updateProduct.submit({ item_template: productName, title })"
							/>
						</div>
					</section>

					<section>
						<div class="mb-2 flex items-baseline gap-2">
							<h2 class="text-base font-medium text-ink-gray-8">Options</h2>
							<span class="text-p-sm text-ink-gray-5">
								{{ liveCount }} of {{ variants.length }} live
							</span>
						</div>

						<div v-if="skippedNotice" class="mb-3 text-p-sm text-ink-amber-3">
							{{ skippedNotice }}
						</div>

						<div class="space-y-2">
							<VariantCard
								v-for="variant in variants"
								:key="variant.name"
								:variant="variant"
								@changed="product.reload()"
							/>
						</div>
					</section>
				</div>

				<aside class="w-full shrink-0 lg:w-72">
					<section class="rounded-lg border border-outline-gray-2 p-4">
						<h2 class="mb-3 text-base font-medium text-ink-gray-8">Status</h2>
						<dl class="space-y-3 text-p-sm">
							<div class="flex items-center justify-between">
								<dt class="text-ink-gray-5">Storefront</dt>
								<dd>
									<Badge
										:theme="liveCount ? 'green' : 'gray'"
										:label="liveCount ? `${liveCount} live` : 'Not live'"
									/>
								</dd>
							</div>
							<div class="flex items-center justify-between">
								<dt class="text-ink-gray-5">Collection</dt>
								<dd class="text-ink-gray-8">{{ product.data.collection }}</dd>
							</div>
							<div class="flex items-center justify-between">
								<dt class="text-ink-gray-5">Price</dt>
								<dd class="text-ink-gray-8">{{ priceLabel }}</dd>
							</div>
							<div class="flex items-center justify-between">
								<dt class="text-ink-gray-5">In stock</dt>
								<dd class="text-ink-gray-8">{{ stockTotal }}</dd>
							</div>
						</dl>

						<a
							v-if="storefrontRoute"
							:href="`/${storefrontRoute}`"
							target="_blank"
							rel="noopener"
							class="mt-4 inline-block text-p-sm text-ink-blue-3 hover:underline"
						>
							View in store →
						</a>
					</section>
				</aside>
			</div>
		</div>
	</div>
</template>
