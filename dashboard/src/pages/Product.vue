<script setup lang="ts">
import VariantCard from "@/components/VariantCard.vue"
import type { ProductVariant } from "@/types"
import { Breadcrumbs, PageHeader, Skeleton, createResource } from "frappe-ui"
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

	<div class="h-full overflow-y-auto px-5 pb-8">
		<div v-if="product.loading && !product.data" class="space-y-3 py-5">
			<Skeleton class="h-9 w-80" />
			<Skeleton class="h-20 w-full" />
			<Skeleton class="h-20 w-full" />
		</div>

		<template v-else-if="product.data">
			<div class="flex max-w-xl items-end gap-2 py-5">
				<FormControl v-model="title" label="Title" class="flex-1" />
				<Button
					:loading="updateProduct.loading"
					:disabled="!titleChanged"
					label="Save"
					@click="updateProduct.submit({ item_template: productName, title })"
				/>
			</div>

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
		</template>
	</div>
</template>
