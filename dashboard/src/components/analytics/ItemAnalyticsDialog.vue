<script setup lang="ts">
import {
	METHOD_PREFIX,
	useAnalyticsRange,
} from "@/composables/useAnalyticsRange"
import type { AnalyticsRangeParams, ItemAnalytics } from "@/types"
import { errorMessage } from "@/utils/errors"
import {
	formatCount,
	formatMoney,
	formatPercent,
	formatShortDate,
} from "@/utils/format"
import { Dialog, useCall } from "frappe-ui"
import { ChartCard, LineChart, NumberCard } from "frappe-ui/charts"
import { computed, watch } from "vue"
import AnalyticsTable from "./AnalyticsTable.vue"
import { type AnalyticsTableColumn, countColumn, moneyColumn } from "./columns"

const props = defineProps<{ itemCode: string | null; currency: string }>()

const open = defineModel<boolean>("open", { required: true })

const { rangeParams, rangeCaption } = useAnalyticsRange()

type DeviceRow = ItemAnalytics["devices"][number]
type SourceRow = ItemAnalytics["sources"][number] & { group: string }
type RecentOrderRow = ItemAnalytics["recent_orders"][number]

const deviceColumns: AnalyticsTableColumn<DeviceRow>[] = [
	{ key: "device", label: "Device" },
	countColumn("views", "Views"),
]

const sourceColumns: AnalyticsTableColumn<SourceRow>[] = [
	{ key: "group", label: "Source" },
	countColumn("views", "Views"),
	countColumn("adds", "Adds"),
]

const orderColumns: AnalyticsTableColumn<RecentOrderRow>[] = [
	{ key: "order", label: "Order" },
	{
		key: "date",
		label: "Date",
		format: (value) => formatShortDate(String(value)),
	},
	countColumn("qty", "Qty"),
	moneyColumn("amount", "Amount", () => props.currency),
]

const itemAnalytics = useCall<
	ItemAnalytics,
	AnalyticsRangeParams & { item_code: string }
>({
	url: `${METHOD_PREFIX}get_item_analytics`,
	params: () => ({ item_code: props.itemCode ?? "", ...rangeParams.value }),
	immediate: false,
})

watch(
	() => props.itemCode,
	(itemCode) => {
		if (itemCode) itemAnalytics.reload()
	},
)

const report = computed(() => itemAnalytics.data)

function storeAverageCaption(totals: ItemAnalytics["totals"]) {
	const direction =
		totals.purchase_to_view_rate >= totals.store_avg_purchase_to_view_rate
			? "above"
			: "below"
	return `${direction} store avg ${formatPercent(totals.store_avg_purchase_to_view_rate)}`
}

const tiles = computed(() => {
	const totals = report.value?.totals
	if (!totals) return []
	return [
		{ title: "Views", value: formatCount(totals.views) },
		{ title: "Adds", value: formatCount(totals.adds) },
		{ title: "Checkouts", value: formatCount(totals.checkouts) },
		{ title: "Units sold", value: formatCount(totals.units_sold) },
		{ title: "Revenue", value: formatMoney(totals.revenue, props.currency) },
		{
			title: "View → purchase",
			value: formatPercent(totals.purchase_to_view_rate),
			caption: storeAverageCaption(totals),
		},
	]
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

const sourceRows = computed<SourceRow[]>(() =>
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
						{{ errorMessage(itemAnalytics.error) }}
					</p>
				</div>

				<template v-else-if="report">
					<div class="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-6">
						<NumberCard
							v-for="tile in tiles"
							:key="tile.title"
							:title="tile.title"
							:value="tile.value"
							:delta-caption="tile.caption"
							:card="false"
						/>
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
							/>
							<p v-else class="text-p-sm text-ink-gray-5">No device data.</p>
						</section>

						<section class="space-y-2">
							<h3 class="text-p-sm font-medium text-ink-gray-8">Top sources</h3>
							<AnalyticsTable
								v-if="sourceRows.length"
								:columns="sourceColumns"
								:rows="sourceRows"
								row-key="group"
							/>
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
