<script setup lang="ts">
import {
	onAnalyticsRefresh,
	useAnalyticsRange,
} from "@/composables/useAnalyticsRange"
import type { SalesTimeseries } from "@/types"
import { formatCount, formatMoney, formatShortDate } from "@/utils/format"
import { useCall } from "frappe-ui"
import { ChartCard, LineChart } from "frappe-ui/charts"
import { computed } from "vue"

const props = defineProps<{ currency: string }>()

const { rangeParams, rangeCaption } = useAnalyticsRange()

const timeseries = useCall<SalesTimeseries>({
	url: "/api/v2/method/ls_shop.api.analytics_dashboard.get_sales_timeseries",
	params: () => rangeParams.value,
	refetch: true,
})

onAnalyticsRefresh(() => timeseries.reload())

const rows = computed(() => {
	const data = timeseries.data
	if (!data) return []
	// A period every store has slept through plots as a flat pair of zero lines, which reads as
	// a broken chart rather than as an empty one - so it is handed no rows at all.
	const hasActivity = data.sales.some(Boolean) || data.orders.some(Boolean)
	if (!hasActivity) return []
	return data.labels.map((day, index) => ({
		day,
		sales: data.sales[index],
		orders: data.orders[index],
	}))
})

const formatSales = (value: number) => formatMoney(value, props.currency, true)
</script>

<template>
	<ChartCard class="h-80">
		<LineChart
			title="Sales over time"
			:subtitle="`Revenue and order volume · ${rangeCaption}`"
			:data="rows"
			x="day"
			:y="['sales', 'orders']"
			:x-axis="{ format: formatShortDate }"
			:y-axis="{ title: 'Sales', format: formatSales }"
			:y2-axis="{ title: 'Orders', format: formatCount }"
			:series-config="{
				sales: { label: 'Sales', type: 'area' },
				orders: { label: 'Orders', axis: 'y2' },
			}"
			:loading="timeseries.loading && !timeseries.data"
			:error="timeseries.error?.message ?? null"
		>
			<template #empty>
				<span class="text-p-sm text-ink-gray-5">
					No orders were placed in this period.
				</span>
			</template>
		</LineChart>
	</ChartCard>
</template>
