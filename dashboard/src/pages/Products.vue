<script setup lang="ts">
import AddProductDialog from "@/components/AddProductDialog.vue"
import { createResource } from "frappe-ui"
import { computed, ref } from "vue"
import { useRouter } from "vue-router"

const router = useRouter()
const showAddProduct = ref(false)

const search = ref("")

const products = createResource({
	url: "ls_shop.api.admin.catalog.get_products",
	makeParams: () => ({ search: search.value }),
	auto: true,
})

const rows = computed(() => products.data?.products ?? [])

function formatPrice(from: number | null, to: number | null) {
	if (from === null || from === undefined) return "No price"
	if (to && to !== from) return `${from} – ${to}`
	return `${from}`
}
</script>

<template>
	<div class="p-6">
		<div class="mb-5 flex items-center justify-between">
			<h1 class="text-xl font-semibold text-ink-gray-9">Products</h1>
			<Button variant="solid" @click="showAddProduct = true">Add product</Button>
		</div>

		<FormControl
			v-model="search"
			type="text"
			placeholder="Search products"
			class="mb-4 max-w-xs"
			@input="products.reload()"
		/>

		<div v-if="products.loading" class="text-base text-ink-gray-5">Loading…</div>

		<div v-else-if="!rows.length" class="text-base text-ink-gray-5">
			No products yet.
		</div>

		<div v-else class="overflow-x-auto rounded border border-outline-gray-2">
			<table class="w-full text-base">
				<thead class="bg-surface-gray-2 text-ink-gray-6">
					<tr>
						<th class="px-3 py-2 text-left font-medium">Product</th>
						<th class="px-3 py-2 text-left font-medium">Collection</th>
						<th class="px-3 py-2 text-left font-medium">Options</th>
						<th class="px-3 py-2 text-left font-medium">Price</th>
						<th class="px-3 py-2 text-left font-medium">Stock</th>
						<th class="px-3 py-2 text-left font-medium">Status</th>
					</tr>
				</thead>
				<tbody>
					<tr
						v-for="row in rows"
						:key="row.name"
						class="cursor-pointer border-t border-outline-gray-2 hover:bg-surface-gray-1"
						@click="router.push({ name: 'Product', params: { name: row.name } })"
					>
						<td class="px-3 py-2">
							<div class="flex items-center gap-2">
								<img
									v-if="row.image"
									:src="row.image"
									alt=""
									class="h-8 w-8 rounded object-cover"
								/>
								<span class="text-ink-gray-8">{{ row.title }}</span>
							</div>
						</td>
						<td class="px-3 py-2 text-ink-gray-6">{{ row.collection }}</td>
						<td class="px-3 py-2 text-ink-gray-6">{{ row.variant_count }}</td>
						<td class="px-3 py-2 text-ink-gray-6">
							{{ formatPrice(row.price_from, row.price_to) }}
						</td>
						<td class="px-3 py-2 text-ink-gray-6">{{ row.stock }}</td>
						<td class="px-3 py-2">
							<Badge
								:theme="row.published_count ? 'green' : 'gray'"
								:label="
									row.published_count
										? `${row.published_count} of ${row.variant_count} live`
										: 'Not live'
								"
							/>
						</td>
					</tr>
				</tbody>
			</table>
		</div>

		<AddProductDialog
			v-model="showAddProduct"
			@created="(name) => router.push({ name: 'Product', params: { name } })"
		/>
	</div>
</template>
