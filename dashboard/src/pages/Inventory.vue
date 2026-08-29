<script setup lang="ts">
import ErrorState from "@/components/ErrorState.vue"
import ListPager from "@/components/ListPager.vue"
import ListSkeleton from "@/components/ListSkeleton.vue"
import { usePagedList } from "@/composables/usePagedList"
import type { InventoryRow } from "@/types"
import { errorMessage } from "@/utils/errors"
import { availabilityTheme, cellAlignClass } from "@/utils/format"
import {
	Badge,
	Breadcrumbs,
	Button,
	FormControl,
	TabButtons,
	TextInput,
	toast,
	useCall,
} from "frappe-ui"
import { ListView } from "frappe-ui/experimental"
import { computed, ref } from "vue"

const availability = ref("low")
const receiveQuantities = ref<Record<string, string>>({})

const tabs = [
	{ label: "Running low", value: "low" },
	{ label: "Out of stock", value: "out" },
	{ label: "All", value: "" },
]

const PAGE_LENGTH = 50

const {
	search,
	request: inventory,
	rows,
	total,
	hasMore,
	loadMore,
	reload,
	getEmptyState,
} = usePagedList<
	{ rows: InventoryRow[]; total: number; low_stock_threshold: number },
	InventoryRow
>(
	"/api/v2/method/ls_shop.api.admin.inventory.get_inventory",
	PAGE_LENGTH,
	(data) => data.rows,
	() => ({ availability: availability.value }),
)

const receiveStock = useCall<
	unknown,
	{ received_quantities: Record<string, string> }
>({
	url: "/api/v2/method/ls_shop.api.admin.inventory.receive_stock",
	method: "POST",
	immediate: false,
	onSuccess: () => {
		toast.success("Stock received")
		receiveQuantities.value = {}
		reload()
	},
	onError: (error: Error) => toast.error(errorMessage(error)),
})

const pendingReceipt = computed(() =>
	Object.fromEntries(
		Object.entries(receiveQuantities.value).filter(
			([, quantity]) => Number(quantity) > 0,
		),
	),
)
const pendingCount = computed(() => Object.keys(pendingReceipt.value).length)

const listOptions = computed(() => ({
	selectable: false,
	showTooltip: false,
	resizeColumn: true,
	emptyState: getEmptyState({
		title: "Nothing running low",
		description: "Every size has healthy stock.",
	}),
}))

const columns = [
	{ label: "Product", key: "product", width: 2.2 },
	{ label: "Variant", key: "option", width: 1.2 },
	{ label: "Size", key: "size", width: 0.7 },
	{ label: "In stock", key: "stock", width: 0.8, align: "right" },
	{ label: "Availability", key: "availability", width: 1.2 },
	{ label: "Receive", key: "receive", width: 1, align: "right" },
]
</script>

<template>
	<div class="flex h-full flex-col bg-surface-base">
		<header
			class="flex min-h-12 items-center justify-between border-b border-outline-gray-1 px-3 sm:px-5"
		>
			<Breadcrumbs :items="[{ label: 'Inventory', route: { name: 'Inventory' } }]" />
		</header>

		<div class="flex items-center gap-3 px-3 py-3 sm:px-5">
			<TabButtons v-model="availability" :options="tabs" />
			<FormControl
				v-model="search"
				type="text"
				placeholder="Search products"
				class="w-56"
			/>
		</div>

		<ListSkeleton
			v-if="inventory.loading && !inventory.data"
			class="px-3 sm:px-5"
			:columns="columns"
		/>

		<ErrorState
			v-else-if="inventory.error"
			class="min-h-0 flex-1"
			title="Could not load your stock"
			:message="errorMessage(inventory.error)"
			@retry="reload"
		/>

		<ListView
			v-else
			class="min-h-0 flex-1 px-3 sm:px-5"
			row-key="item_code"
			:columns="columns"
			:rows="rows"
			:options="listOptions"
		>
			<template #cell="{ item, row, column }">
				<Badge
					v-if="column.key === 'availability'"
					variant="subtle"
					:theme="availabilityTheme(row.availability)"
					:label="row.availability"
				/>
				<TextInput
					v-else-if="column.key === 'receive'"
					class="ms-auto w-20 [&_[data-slot=control]]:text-right"
					type="number"
					placeholder="0"
					:aria-label="`Receive stock for ${row.product} ${row.size}`"
					:model-value="receiveQuantities[row.item_code] ?? ''"
					@click.stop
					@update:model-value="receiveQuantities[row.item_code] = $event"
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
			v-if="inventory.data && rows.length"
			:loaded="rows.length"
			:total="total"
			noun="sizes"
			:has-more="hasMore"
			:loading="inventory.loading"
			@load-more="loadMore"
		/>

		<div
			v-if="pendingCount"
			class="flex items-center gap-2 border-t border-outline-gray-1 px-3 py-3 sm:px-5"
		>
			<span class="mr-auto text-sm text-ink-gray-5">
				Receiving {{ pendingCount }} {{ pendingCount === 1 ? "size" : "sizes" }}
			</span>
			<Button label="Discard" @click="receiveQuantities = {}" />
			<Button
				variant="solid"
				theme="gray"
				icon-left="lucide-package-plus"
				:loading="receiveStock.loading"
				label="Receive stock"
				@click="receiveStock.submit({ received_quantities: pendingReceipt })"
			/>
		</div>
	</div>
</template>
