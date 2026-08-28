<script setup lang="ts">
import { useAnalyticsRange } from "@/composables/useAnalyticsRange"
import type { AnalyticsRangeParams, ItemAnalytics } from "@/types"
import {
	formatCount,
	formatMoney,
	formatPercent,
	formatShortDate,
} from "@/utils/format"
import { Dialog, useCall } from "frappe-ui"
import { ChartCard, LineChart } from "frappe-ui/charts"
import { computed, watch } from "vue"
import AnalyticsTable from "./AnalyticsTable.vue"
import type { AnalyticsTableColumn } from "./AnalyticsTable.vue"
import StatChip from "./StatChip.vue"

const props = defineProps<{ itemCode: string | null; currency: string }>()

const open = defineModel<boolean>("open", { required: true })

const { rangeParams, rangeCaption } = useAnalyticsRange()

const deviceColumns: AnalyticsTableColumn[] = [
	{ key: "device", label: "Device" },
	{ key: "views", label: "Views", numeric: true },
]

const sourceColumns: AnalyticsTableColumn[] = [
	{ key: "source", label: "Source" },
	{ key: "views", label: "Views", numeric: true },
	{ key: "adds", label: "Adds", numeric: true },
]

const orderColumns: AnalyticsTableColumn[] = [
	{ key: "order", label: "Order" },
	{ key: "date", label: "Date" },
	{ key: "qty", label: "Qty", numeric: true },
	{ key: "amount", label: "Amount", numeric: true },
]

const itemAnalytics = useCall<
	ItemAnalytics,
	AnalyticsRangeParams & { item_code: string }
>({
	url: "/api/v2/method/ls_shop.api.analytics_dashboard.get_item_analytics",
	params: () => ({ item_code: props.itemCode ?? "", ...rangeParams.value }),
	immediate: false,
})

// Fetching is driven by the item rather than by the params: an open dialog must not refetch
// itself out from under the reader, and a closed one must not fetch at all.
watch(
	() => props.itemCode,
	(itemCode) => {
		if (itemCode) itemAnalytics.reload()
	},
)

const report = computed(() => itemAnalytics.data)

const chips = computed(() => {
	const totals = report.value?.totals
	if (!totals) return []
	return [
		{ label: "Views", value: formatCount(totals.views) },
		{ label: "Adds", value: formatCount(totals.adds) },
		{ label: "Checkouts", value: formatCount(totals.checkouts) },
		{ label: "Units sold", value: formatCount(totals.units_sold) },
		{ label: "Revenue", value: formatMoney(totals.revenue, props.currency) },
		{
			label: "View → purchase",
			value: formatPercent(totals.purchase_to_view_rate),
		},
	]
})

/** The one comparison that makes a single product's rate mean anything. */
const storeAverageCaption = computed(() => {
	const totals = report.value?.totals
	if (!totals) return ""
	const above =
		totals.purchase_to_view_rate >= totals.store_avg_purchase_to_view_rate
	const direction = above ? "above" : "below"
	return `${direction} store avg ${formatPercent(totals.store_avg_purchase_to_view_rate)}`
})

const dailyRows = computed(() => {
	const daily = report.value?.daily
	if (!daily) return []
	const hasActivity =
		daily.views.some(Boolean) ||
		daily.adds.some(Boolean) ||
		daily.units.some(Boolean)
	if (!hasActivity) return []
	return daily.labels.map((day, index) => ({
		day,
		views: daily.views[index],
		adds: daily.adds[index],
		units: daily.units[index],
	}))
})

const sourceRows = computed(() =>
	(report.value?.sources ?? []).map((row) => ({
		...row,
		group: row.medium ? `${row.source} / ${row.medium}` : row.source,
	})),
)
</script>

<template>
	<Dialog
		v-model:open="open"
		size="4xl"
		:title="report?.item_name || itemCode || 'Product analytics'"
	>
		<template #default>
			<div class="space-y-4">
				<p class="text-p-sm text-ink-gray-5">{{ rangeCaption }}</p>

				<div v-if="itemAnalytics.loading" class="py-10 text-center">
					<span class="text-p-sm text-ink-gray-5">Loading product report…</span>
				</div>

				<div v-else-if="itemAnalytics.error" class="py-10 text-center">
					<p class="text-sm-medium text-ink-red-7">
						Could not load this product report
					</p>
					<p class="mt-1 text-p-sm text-ink-gray-5">
						{{ itemAnalytics.error.message }}
					</p>
				</div>

				<template v-else-if="report">
					<div class="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-6">
						<StatChip
							v-for="chip in chips"
							:key="chip.label"
							:label="chip.label"
							:value="chip.value"
						>
							<span
								v-if="chip.label === 'View → purchase'"
								class="mt-0.5 block truncate text-p-xs text-ink-gray-5"
							>
								{{ storeAverageCaption }}
							</span>
						</StatChip>
					</div>

					<ChartCard class="h-72">
						<LineChart
							title="Daily activity"
							:data="dailyRows"
							x="day"
							:y="['views', 'adds', 'units']"
							:x-axis="{ format: formatShortDate }"
							:y-axis="{ format: formatCount }"
							:series-config="{
								views: { label: 'Views' },
								adds: { label: 'Adds' },
								units: { label: 'Units sold' },
							}"
						>
							<template #empty>
								<span class="text-p-sm text-ink-gray-5">
									No daily activity in this period.
								</span>
							</template>
						</LineChart>
					</ChartCard>

					<div class="grid grid-cols-1 gap-4 lg:grid-cols-2">
						<section class="space-y-2">
							<h3 class="text-p-sm font-medium text-ink-gray-8">Devices</h3>
							<AnalyticsTable
								v-if="report.devices.length"
								:columns="deviceColumns"
								:rows="report.devices"
								row-key="device"
							>
								<template #views="{ row }">
									{{ formatCount(Number(row.views)) }}
								</template>
							</AnalyticsTable>
							<p v-else class="text-p-sm text-ink-gray-5">No device data.</p>
						</section>

						<section class="space-y-2">
							<h3 class="text-p-sm font-medium text-ink-gray-8">Top sources</h3>
							<AnalyticsTable
								v-if="sourceRows.length"
								:columns="sourceColumns"
								:rows="sourceRows"
								row-key="group"
							>
								<template #source="{ row }">{{ row.group }}</template>
								<template #views="{ row }">
									{{ formatCount(Number(row.views)) }}
								</template>
								<template #adds="{ row }">
									{{ formatCount(Number(row.adds)) }}
								</template>
							</AnalyticsTable>
							<p v-else class="text-p-sm text-ink-gray-5">No source data.</p>
						</section>
					</div>

					<section class="space-y-2">
						<h3 class="text-p-sm font-medium text-ink-gray-8">Recent orders</h3>
						<AnalyticsTable
							v-if="report.recent_orders.length"
							:columns="orderColumns"
							:rows="report.recent_orders"
							row-key="order"
						>
							<template #order="{ row }">
								<a
									class="text-ink-blue-link hover:underline"
									:href="`/app/sales-order/${row.order}`"
									target="_blank"
									rel="noopener"
								>
									{{ row.order }}
								</a>
							</template>
							<template #date="{ row }">
								{{ formatShortDate(String(row.date)) }}
							</template>
							<template #qty="{ row }">{{ formatCount(Number(row.qty)) }}</template>
							<template #amount="{ row }">
								{{ formatMoney(Number(row.amount), props.currency) }}
							</template>
						</AnalyticsTable>
						<p v-else class="text-p-sm text-ink-gray-5">
							No orders in this period.
						</p>
					</section>
				</template>
			</div>
		</template>
	</Dialog>
</template>
