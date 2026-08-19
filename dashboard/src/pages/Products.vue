<script setup lang="ts">
import AddProductDialog from "@/components/AddProductDialog.vue"
import type { ProductRow } from "@/types"
import {
	Avatar,
	Badge,
	Breadcrumbs,
	ListView,
	PageHeader,
	createResource,
} from "frappe-ui"
import { computed, ref, watch } from "vue"
import { useRouter } from "vue-router"

const router = useRouter()
const showAddProduct = ref(false)
const search = ref("")

const products = createResource({
	url: "ls_shop.api.admin.catalog.get_products",
	makeParams: () => ({ search: search.value }),
	auto: true,
})

// Typing should not fire a request per keystroke; wait until the owner pauses.
let searchTimer: ReturnType<typeof setTimeout>
watch(search, () => {
	clearTimeout(searchTimer)
	searchTimer = setTimeout(() => products.reload(), 300)
})

const rows = computed<ProductRow[]>(() => products.data?.products ?? [])

function formatPrice(row: ProductRow) {
	if (row.price_from === null) return "—"
	if (row.price_to && row.price_to !== row.price_from) {
		return `${row.price_from} – ${row.price_to}`
	}
	return String(row.price_from)
}

const columns = [
	{
		label: "Product",
		key: "title",
		width: 3,
		prefix: ({ row }: { row: ProductRow }) =>
			h(Avatar, {
				shape: "square",
				image: row.image ?? undefined,
				label: row.title,
				size: "sm",
			}),
	},
	{ label: "Collection", key: "collection", width: 1.5 },
	{ label: "Options", key: "variant_count", width: 0.8 },
	{ label: "Price", key: "price", width: 1.2 },
	{ label: "Stock", key: "stock", width: 0.8 },
	{ label: "Status", key: "status", width: 1.2 },
]

const listOptions = {
	getRowRoute: (row: ProductRow) => ({
		name: "Product",
		params: { name: row.name },
	}),
	showTooltip: false,
	emptyState: {
		title: "No products yet",
		description: "Add your first product to start selling.",
		button: {
			label: "Add product",
			variant: "solid",
			onClick: () => {
				showAddProduct.value = true
			},
		},
	},
}
</script>

<template>
	<PageHeader>
		<Breadcrumbs :items="[{ label: 'Products', route: { name: 'Products' } }]" />
		<Button variant="solid" label="Add product" @click="showAddProduct = true" />
	</PageHeader>

	<div class="flex h-full flex-col px-5 pb-5">
		<div class="py-3">
			<FormControl v-model="search" type="text" placeholder="Search products" class="max-w-xs" />
		</div>

		<ListView
			class="min-h-0 flex-1"
			row-key="name"
			:columns="columns"
			:rows="rows"
			:options="listOptions"
		>
			<template #cell="{ item, row, column }">
				<div v-if="column.key === 'title'" class="flex min-w-0 items-center gap-2.5">
					<img
						v-if="row.image"
						:src="row.image"
						alt=""
						class="size-7 shrink-0 rounded object-cover"
					/>
					<div
						v-else
						class="grid size-7 shrink-0 place-items-center rounded bg-surface-gray-2 text-p-xs text-ink-gray-4"
					>
						{{ row.title.slice(0, 1) }}
					</div>
					<span class="truncate text-ink-gray-8">{{ row.title }}</span>
				</div>
				<Badge
					v-else-if="column.key === 'status'"
					:theme="row.published_count ? 'green' : 'gray'"
					:label="
						row.published_count
							? `${row.published_count} of ${row.variant_count} live`
							: 'Not live'
					"
				/>
				<span v-else-if="column.key === 'price'" class="text-ink-gray-7">
					{{ formatPrice(row) }}
				</span>
				<span v-else class="truncate text-ink-gray-7">{{ item }}</span>
			</template>
		</ListView>

		<AddProductDialog
			v-model="showAddProduct"
			@created="(name) => router.push({ name: 'Product', params: { name } })"
		/>
	</div>
</template>
