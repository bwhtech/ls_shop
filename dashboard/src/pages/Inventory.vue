<script setup lang="ts">
import ListSkeleton from "@/components/ListSkeleton.vue"
import type { InventoryRow } from "@/types"
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
import { computed, ref, watch } from "vue"

const search = ref("")
const availability = ref("low")
const receiveQuantities = ref<Record<string, string>>({})

const tabs = [
	{ label: "Running low", value: "low" },
	{ label: "Out of stock", value: "out" },
	{ label: "All", value: "" },
]

const inventory = useCall<{
	rows: InventoryRow[]
	total: number
	low_stock_threshold: number
}>({
	url: "/api/v2/method/ls_shop.api.admin.inventory.get_inventory",
	params: () => ({ availability: availability.value, search: search.value }),
	refetch: true,
})

let searchTimer: ReturnType<typeof setTimeout>
watch(search, () => {
	clearTimeout(searchTimer)
	searchTimer = setTimeout(() => inventory.reload(), 300)
})

const receiveStock = useCall({
	url: "/api/v2/method/ls_shop.api.admin.inventory.receive_stock",
	method: "POST",
	immediate: false,
	onSuccess: () => {
		toast.success("Stock received")
		receiveQuantities.value = {}
		inventory.reload()
	},
	onError: (error: Error) => toast.error(error.message),
})

const rows = computed(() => inventory.data?.rows ?? [])
const pending = computed(() =>
	Object.entries(receiveQuantities.value).filter(
		([, quantity]) => Number(quantity) > 0,
	),
)

const columns = [
	{ label: "Product", key: "product", width: 2.2 },
	{ label: "Option", key: "option", width: 1.2 },
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
			<TabButtons v-model="availability" :buttons="tabs" />
			<FormControl
				v-model="search"
				type="text"
				placeholder="Search products"
				class="w-56"
			/>
			<span class="ml-auto text-sm text-ink-gray-5">{{ inventory.data?.total ?? 0 }} sizes</span>
		</div>

		<ListSkeleton v-if="inventory.loading && !rows.length" class="px-3 sm:px-5" />

		<ListView
			v-else
			class="min-h-0 flex-1 px-3 sm:px-5"
			row-key="item_code"
			:columns="columns"
			:rows="rows"
			:options="{
				selectable: false,
				showTooltip: false,
				resizeColumn: true,
				emptyState: {
					title: 'Nothing running low',
					description: 'Every size has healthy stock.',
				},
			}"
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

		<!-- One receipt covers whatever the owner typed across the whole screen, so a stock take
		     is a single action rather than one submission per size. -->
		<div
			v-if="pending.length"
			class="flex items-center gap-2 border-t border-outline-gray-1 px-3 py-3 sm:px-5"
		>
			<span class="mr-auto text-sm text-ink-gray-5">
				Receiving {{ pending.length }} {{ pending.length === 1 ? "size" : "sizes" }}
			</span>
			<Button label="Discard" @click="receiveQuantities = {}" />
			<Button
				variant="solid"
				theme="gray"
				icon-left="lucide-package-plus"
				:loading="receiveStock.loading"
				label="Receive stock"
				@click="receiveStock.submit({ received_quantities: receiveQuantities })"
			/>
		</div>
	</div>
</template>
