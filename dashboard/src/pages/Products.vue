<script setup lang="ts">
import ListSkeleton from "@/components/ListSkeleton.vue"
import AddProductDialog from "@/components/AddProductDialog.vue"
import type { ProductRow } from "@/types"
import { formatRowPrice, publishTheme } from "@/utils/format"
import {
	Badge,
	Breadcrumbs,
	Button,
	FormControl,
	ListView,
	useCall,
} from "frappe-ui"
import { computed, ref, watch } from "vue"
import { useRouter } from "vue-router"

const router = useRouter()
const showAddProduct = ref(false)
const search = ref("")

const products = useCall<{ products: ProductRow[]; total: number }>({
	url: "/api/v2/method/ls_shop.api.admin.catalog.get_products",
	params: () => ({ search: search.value }),
})

// Typing should not fire a request per keystroke; wait until the owner pauses.
let searchTimer: ReturnType<typeof setTimeout>
watch(search, () => {
	clearTimeout(searchTimer)
	searchTimer = setTimeout(() => products.reload(), 300)
})

const rows = computed(() =>
	(products.data?.products ?? []).map((product) => ({
		...product,
		price: formatRowPrice(product),
		status: product.published_count
			? `${product.published_count} of ${product.variant_count} live`
			: "Not live",
	})),
)

const columns = [
	{ label: "Product", key: "title", width: 3 },
	{ label: "Collection", key: "collection", width: 1.5 },
	{ label: "Options", key: "variant_count", width: 0.7, align: "right" },
	{ label: "Price", key: "price", width: 1.2, align: "right" },
	{ label: "Stock", key: "stock", width: 0.8, align: "right" },
	{ label: "Status", key: "status", width: 1.3 },
]

const listOptions = {
	getRowRoute: (row: ProductRow) => ({
		name: "Product",
		params: { name: row.name },
	}),
	// Selection stays off until a bulk action consumes it.
	selectable: false,
	showTooltip: false,
	resizeColumn: true,
	emptyState: {
		title: "No products yet",
		description: "Add your first product to start selling.",
		button: {
			label: "Add product",
			// Subtle, not solid: the page header already carries the one solid primary, and a
			// second solid gray button inverts to near-white in dark mode.
			variant: "subtle",
			theme: "gray",
			onClick: () => {
				showAddProduct.value = true
			},
		},
	},
}
</script>

<template>
	<div class="flex h-full flex-col bg-surface-base">
		<header
			class="flex min-h-12 items-center justify-between border-b border-outline-gray-1 px-3 sm:px-5"
		>
			<Breadcrumbs :items="[{ label: 'Products', route: { name: 'Products' } }]" />
			<Button
				variant="solid"
				theme="gray"
				icon-left="lucide-plus"
				label="Add product"
				@click="showAddProduct = true"
			/>
		</header>

		<div class="px-3 py-3 sm:px-5">
			<FormControl
				v-model="search"
				type="text"
				placeholder="Search products"
				class="w-56"
			/>
		</div>

		<ListSkeleton v-if="products.loading && !rows.length" class="px-3 sm:px-5" />

		<ListView
			v-else
			class="min-h-0 flex-1 px-3 sm:px-5"
			row-key="name"
			:columns="columns"
			:rows="rows"
			:options="listOptions"
		>
			<!-- The #cell slot replaces ListView's default rendering for every column, a column's
			     own prefix included, so the thumbnail is drawn here rather than declared there. -->
			<template #cell="{ item, row, column }">
				<div v-if="column.key === 'title'" class="flex min-w-0 items-center gap-2.5">
					<img
						v-if="row.image"
						:src="row.image"
						alt=""
						class="size-6 shrink-0 rounded object-cover"
					/>
					<div
						v-else
						class="grid size-6 shrink-0 place-items-center rounded bg-surface-gray-2 text-2xs text-ink-gray-4"
					>
						{{ row.title.slice(0, 1) }}
					</div>
					<span class="truncate text-base text-ink-gray-9">{{ row.title }}</span>
				</div>

				<Badge
					v-else-if="column.key === 'status'"
					variant="subtle"
					:theme="publishTheme(row.published_count)"
					:label="row.status"
				/>

				<span v-else class="truncate text-base text-ink-gray-7">{{ item }}</span>
			</template>
		</ListView>

		<AddProductDialog
			v-model:open="showAddProduct"
			@created="(name) => router.push({ name: 'Product', params: { name } })"
		/>
	</div>
</template>
