<script setup lang="ts">
import type { OrderRow } from "@/types"
import { orderStateTheme } from "@/utils/format"
import {
	Badge,
	Breadcrumbs,
	FormControl,
	ListView,
	TabButtons,
	useCall,
} from "frappe-ui"
import { computed, ref, watch } from "vue"

const search = ref("")
const status = ref("open")

const statusTabs = [
	{ label: "To fulfil", value: "open" },
	{ label: "Fulfilled", value: "fulfilled" },
	{ label: "Cancelled", value: "cancelled" },
	{ label: "All", value: "" },
]

const orders = useCall<{ orders: OrderRow[]; total: number }>({
	url: "/api/v2/method/ls_shop.api.admin.orders.get_orders",
	params: () => ({ status: status.value, search: search.value }),
	refetch: true,
})

let searchTimer: ReturnType<typeof setTimeout>
watch(search, () => {
	clearTimeout(searchTimer)
	searchTimer = setTimeout(() => orders.reload(), 300)
})

const rows = computed(() =>
	(orders.data?.orders ?? []).map((order) => ({
		...order,
		items: `${order.item_count}`,
		amount: `${order.currency} ${order.total}`,
	})),
)

const columns = [
	{ label: "Order", key: "name", width: 1.6 },
	{ label: "Customer", key: "customer", width: 2 },
	{ label: "Placed", key: "placed_on", width: 1.2 },
	{ label: "Items", key: "items", width: 0.7, align: "right" },
	{ label: "Total", key: "amount", width: 1.3, align: "right" },
	{ label: "Status", key: "state", width: 1.2 },
]

const listOptions = {
	getRowRoute: (row: OrderRow) => ({
		name: "Order",
		params: { name: row.name },
	}),
	// No bulk action exists for orders yet, and a checkbox that does nothing is just noise.
	selectable: false,
	showTooltip: false,
	resizeColumn: true,
	emptyState: {
		title: "No orders here",
		description: "Orders placed in your store will show up here.",
	},
}
</script>

<template>
	<div class="flex h-full flex-col bg-surface-base">
		<header
			class="flex min-h-12 items-center justify-between border-b border-outline-gray-1 px-3 sm:px-5"
		>
			<Breadcrumbs :items="[{ label: 'Orders', route: { name: 'Orders' } }]" />
		</header>

		<div class="flex items-center gap-3 px-3 py-3 sm:px-5">
			<TabButtons v-model="status" :buttons="statusTabs" />
			<FormControl
				v-model="search"
				type="text"
				placeholder="Search orders"
				class="w-56"
			/>
		</div>

		<ListView
			class="min-h-0 flex-1 px-3 sm:px-5"
			row-key="name"
			:columns="columns"
			:rows="rows"
			:loading="orders.loading"
			:options="listOptions"
		>
			<template #cell="{ item, row, column }">
				<Badge
					v-if="column.key === 'state'"
					variant="subtle"
					:theme="orderStateTheme(row.state)"
					:label="row.state"
				/>
				<span
					v-else-if="column.key === 'name'"
					class="truncate text-base text-ink-gray-9"
					>{{ row.name }}</span
				>
				<span v-else class="truncate text-base text-ink-gray-7">{{ item }}</span>
			</template>
		</ListView>
	</div>
</template>
