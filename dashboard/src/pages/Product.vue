<script setup lang="ts">
import VariantCard from "@/components/VariantCard.vue"
import type { ProductVariant } from "@/types"
import { createResource } from "frappe-ui"
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

const allLive = computed(
	() =>
		product.data?.variants?.length > 0 &&
		product.data.variants.every(
			(variant: ProductVariant) => variant.is_published,
		),
)
</script>

<template>
	<div v-if="product.data" class="p-6">
		<div class="mb-5 flex items-center gap-3">
			<router-link
				:to="{ name: 'Products' }"
				class="text-base text-ink-gray-5 hover:text-ink-gray-7"
			>
				Products
			</router-link>
			<span class="text-ink-gray-4">/</span>
			<h1 class="text-xl font-semibold text-ink-gray-9">{{ product.data.title }}</h1>
		</div>

		<div class="mb-6 flex max-w-md items-end gap-2">
			<FormControl v-model="title" label="Title" class="flex-1" />
			<Button
				:loading="updateProduct.loading"
				@click="updateProduct.submit({ item_template: productName, title })"
			>
				Save
			</Button>
		</div>

		<div class="mb-2 flex items-center justify-between">
			<h2 class="text-base font-medium text-ink-gray-8">Options</h2>
			<Button
				variant="solid"
				:loading="publishAll.loading"
				@click="
					publishAll.submit({ item_template: productName, publish: allLive ? 0 : 1 })
				"
			>
				{{ allLive ? "Unpublish all" : "Publish all" }}
			</Button>
		</div>

		<div v-if="skippedNotice" class="mb-3 text-p-sm text-ink-amber-3">
			{{ skippedNotice }}
		</div>

		<div class="space-y-2">
			<VariantCard
				v-for="variant in product.data.variants"
				:key="variant.name"
				:variant="variant"
				@changed="product.reload()"
			/>
		</div>
	</div>
</template>
