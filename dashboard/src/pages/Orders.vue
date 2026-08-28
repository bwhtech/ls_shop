<script setup lang="ts">
import ErrorState from "@/components/ErrorState.vue"
import ListPager from "@/components/ListPager.vue"
import ListSkeleton from "@/components/ListSkeleton.vue"
import OrderStateBadge from "@/components/OrderStateBadge.vue"
import { usePagedList } from "@/composables/usePagedList"
import type { OrderRow } from "@/types"
import { errorMessage } from "@/utils/errors"
import { cellAlignClass, formatMoney } from "@/utils/format"
import { Breadcrumbs, FormControl, TabButtons } from "frappe-ui"
import { ListView } from "frappe-ui/experimental"
import { computed, ref } from "vue"

const status = ref("open")

const statusTabs = [
	{ label: "To fulfil", value: "open" },
	{ label: "Fulfilled", value: "fulfilled" },
	{ label: "Cancelled", value: "cancelled" },
	{ label: "All", value: "" },
]

// Matches the endpoint's own default, so the first screenful is the page it already returns.
const PAGE_LENGTH = 20

const {
	search,
	request: orders,
	rows: loadedOrders,
	total,
	hasMore,
	loadMore,
	reload,
	getEmptyState,
} = usePagedList<{ orders: OrderRow[]; total: number }, OrderRow>(
	"/api/v2/method/ls_shop.api.admin.orders.get_orders",
	PAGE_LENGTH,
	(data) => data.orders,
	() => ({ status: status.value }),
)

const rows = computed(() =>
	loadedOrders.value.map((order) => ({
		...order,
		items: `${order.item_count}`,
		amount: formatMoney(order.total, order.currency),
	})),
)

const columns = [
	{ label: "Order", key: "name", width: 1.6 },
	{ label: "Customer", key: "customer", width: 2 },
	{ label: "Placed", key: "placed_on", width: 1.2 },
	{ label: "Items", key: "items", width: 0.7, align: "right" },
	{ label: "Total", key: "amount", width: 1.3, align: "right" },
	{ label: "Status", key: "state", width: 1.8 },
]

const listOptions = computed(() => ({
	getRowRoute: (row: OrderRow) => ({
		name: "Order",
		params: { name: row.name },
	}),
	// No bulk action exists for orders yet, and a checkbox that does nothing is just noise.
	selectable: false,
	showTooltip: false,
	resizeColumn: true,
	emptyState: getEmptyState({
		title: "No orders here",
		description: "Orders placed in your store will show up here.",
	}),
}))
</script>

<template>
	<div class="flex h-full flex-col bg-surface-base">
		<header
			class="flex min-h-12 items-center justify-between border-b border-outline-gray-1 px-3 sm:px-5"
		>
			<Breadcrumbs :items="[{ label: 'Orders', route: { name: 'Orders' } }]" />
		</header>

		<div class="flex items-center gap-3 px-3 py-3 sm:px-5">
			<TabButtons v-model="status" :options="statusTabs" />
			<FormControl
				v-model="search"
				type="text"
				placeholder="Search orders"
				class="w-56"
			/>
		</div>

		<ListSkeleton
			v-if="orders.loading && !orders.data"
			class="px-3 sm:px-5"
			:columns="columns"
		/>

		<ErrorState
			v-else-if="orders.error"
			class="min-h-0 flex-1"
			title="Could not load your orders"
			:message="errorMessage(orders.error)"
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
			<template #cell="{ item, row, column }">
				<OrderStateBadge
					v-if="column.key === 'state'"
					:state="row.state"
				/>
				<span
					v-else-if="column.key === 'name'"
					class="truncate text-base text-ink-gray-9"
					>{{ row.name }}</span
				>
				<span
					v-else
					class="truncate text-base text-ink-gray-7"
					:class="cellAlignClass(column.align)"
					>{{ item }}</span
				>
			</template>
		</ListView>

		<ListPager
			v-if="orders.data && rows.length"
			:loaded="rows.length"
			:total="total"
			noun="orders"
			:has-more="hasMore"
			:loading="orders.loading"
			@load-more="loadMore"
		/>
	</div>
</template>
