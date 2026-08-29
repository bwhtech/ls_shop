<script setup lang="ts">
import AddProductDialog from "@/components/AddProductDialog.vue"
import ErrorState from "@/components/ErrorState.vue"
import ListPager from "@/components/ListPager.vue"
import ListSkeleton from "@/components/ListSkeleton.vue"
import { showAddProduct } from "@/components/addProduct"
import { usePagedList } from "@/composables/usePagedList"
import type { ProductRow } from "@/types"
import { errorMessage } from "@/utils/errors"
import { cellAlignClass, formatRowPrice, publishTheme } from "@/utils/format"
import { Badge, Breadcrumbs, Button, FormControl } from "frappe-ui"
import { ListView } from "frappe-ui/experimental"
import { computed } from "vue"
import { useRouter } from "vue-router"

const router = useRouter()

const PAGE_LENGTH = 20

const {
	search,
	request: products,
	rows: loadedProducts,
	total,
	hasMore,
	loadMore,
	reload,
	getEmptyState,
} = usePagedList<
	{ products: ProductRow[]; total: number; currency: string },
	ProductRow
>(
	"/api/v2/method/ls_shop.api.admin.catalog.get_products",
	PAGE_LENGTH,
	(data) => data.products,
)

const currency = computed(() => products.data?.currency ?? "")

const rows = computed(() =>
	loadedProducts.value.map((product) => ({
		...product,
		price: formatRowPrice(product, currency.value),
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

const listOptions = computed(() => ({
	getRowRoute: (row: ProductRow) => ({
		name: "Product",
		params: { name: row.name },
	}),
	selectable: false,
	showTooltip: false,
	resizeColumn: true,
	emptyState: getEmptyState({
		title: "No products yet",
		description: "Add your first product to start selling.",
		button: {
			label: "Add product",
			// Subtle, not solid: a second solid gray button inverts to near-white in dark mode.
			variant: "subtle",
			theme: "gray",
			onClick: () => {
				showAddProduct.value = true
			},
		},
	}),
}))
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

		<ListSkeleton
			v-if="products.loading && !products.data"
			class="px-3 sm:px-5"
			:columns="columns"
		/>

		<ErrorState
			v-else-if="products.error"
			class="min-h-0 flex-1"
			title="Could not load your products"
			:message="errorMessage(products.error)"
			@retry="reload"
		/>

		<ListView
			v-else
			class="min-h-0 flex-1 px-3 sm:px-5"
			row-key="name"
			:columns="columns"
			:rows="rows"
			:options="listOptions"
		>
			<!-- The #cell slot replaces ListView's default rendering for every column, a column's own prefix included. -->
			<template #cell="{ item, row, column }">
				<div v-if="column.key === 'title'" class="flex min-w-0 items-center gap-2.5">
					<img
						v-if="row.image"
						:src="row.image"
						alt=""
						class="size-6 shrink-0 rounded-4 object-cover"
					/>
					<div
						v-else
						class="grid size-6 shrink-0 place-items-center rounded-4 bg-surface-gray-2 text-2xs text-ink-gray-4"
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

				<span
					v-else
					class="truncate text-base text-ink-gray-7"
					:class="cellAlignClass(column.align)"
					>{{ item }}</span
				>
			</template>
		</ListView>

		<ListPager
			v-if="products.data && rows.length"
			:loaded="rows.length"
			:total="total"
			noun="products"
			:has-more="hasMore"
			:loading="products.loading"
			@load-more="loadMore"
		/>

		<AddProductDialog
			v-model:open="showAddProduct"
			@created="(name) => router.push({ name: 'Product', params: { name } })"
		/>
	</div>
</template>
