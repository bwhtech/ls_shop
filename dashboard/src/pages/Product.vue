<script setup lang="ts">
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

const setPublished = createResource({
	url: "ls_shop.api.admin.catalog.set_variant_published",
	onSuccess: () => product.reload(),
})

const publishError = computed(() => setPublished.error?.messages?.[0])
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

		<h2 class="mb-2 text-base font-medium text-ink-gray-8">Options</h2>
		<ErrorMessage class="mb-2" :message="publishError" />

		<div class="space-y-2">
			<div
				v-for="variant in product.data.variants"
				:key="variant.name"
				class="flex items-center justify-between rounded border border-outline-gray-2 px-4 py-3"
			>
				<div>
					<div class="text-base text-ink-gray-8">{{ variant.option }}</div>
					<div class="text-p-sm text-ink-gray-5">
						{{ variant.sizes.length }} sizes · {{ variant.images.length }} images
					</div>
					<div v-if="variant.blockers.length" class="mt-1 text-p-sm text-ink-amber-3">
						{{ variant.blockers.join(" · ") }}
					</div>
				</div>
				<div class="flex items-center gap-3">
					<Badge
						:theme="variant.is_published ? 'green' : 'gray'"
						:label="variant.is_published ? 'Live' : 'Not live'"
					/>
					<Button
						:loading="setPublished.loading"
						:disabled="!variant.is_published && variant.blockers.length > 0"
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
		</div>
	</div>
</template>
