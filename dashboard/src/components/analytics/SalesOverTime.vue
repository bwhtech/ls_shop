<script setup lang="ts">
import {
	useAnalyticsRange,
	useAnalyticsReport,
} from "@/composables/useAnalyticsRange"
import type { SalesTimeseries } from "@/types"
import { formatCount, formatDate, formatMoney } from "@/utils/format"
import { ChartCard, LineChart } from "frappe-ui/charts"
import { computed } from "vue"

const props = defineProps<{ currency: string }>()

const { rangeCaption } = useAnalyticsRange()

const { data, loading, error } = useAnalyticsReport<SalesTimeseries>(
	"get_sales_timeseries",
)

const rows = computed(() => {
	const timeseries = data.value
	if (!timeseries) return []
	const hasActivity =
		timeseries.sales.some(Boolean) || timeseries.orders.some(Boolean)
	if (!hasActivity) return []
	return timeseries.labels.map((day, index) => ({
		day,
		sales: timeseries.sales[index],
		orders: timeseries.orders[index],
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
			:x-axis="{ format: formatDate }"
			:y-axis="{ title: 'Sales', format: formatSales }"
			:y2-axis="{ title: 'Orders', format: formatCount }"
			:series-config="{
				sales: { label: 'Sales', type: 'area' },
				orders: { label: 'Orders', axis: 'y2' },
			}"
			:loading="loading"
			:error="error"
		>
			<template #empty>
				<span class="text-p-sm text-ink-gray-5">
					No orders were placed in this period.
				</span>
			</template>
		</LineChart>
	</ChartCard>
</template>
