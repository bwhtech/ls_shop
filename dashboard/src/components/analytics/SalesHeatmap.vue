<script setup lang="ts">
import {
	useAnalyticsRange,
	useAnalyticsReport,
} from "@/composables/useAnalyticsRange"
import type { SalesHeatmap } from "@/types"
import { formatCount } from "@/utils/format"
import { ChartCard, HeatmapChart } from "frappe-ui/charts"
import { computed } from "vue"

const { rangeCaption } = useAnalyticsRange()

// Row 0 of the matrix is Monday, the way the API builds it from `weekday()`.
const weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
const hours = Array.from(
	{ length: 24 },
	(_, hour) => `${String(hour).padStart(2, "0")}:00`,
)

const { data, loading, error } =
	useAnalyticsReport<SalesHeatmap>("get_sales_heatmap")

const cells = computed(() => {
	const heatmap = data.value
	// A grid of 168 zeroes colours as one flat block; it is an empty chart, not a cold week.
	if (!heatmap?.max) return []
	return heatmap.matrix.flatMap((row, weekday) =>
		row.map((orders, hour) => ({
			weekday: weekdays[weekday],
			hour: hours[hour],
			orders,
		})),
	)
})
</script>

<template>
	<ChartCard class="h-96">
		<HeatmapChart
			title="Sales by hour"
			:subtitle="`When your customers order, across the week · ${rangeCaption}`"
			:data="cells"
			x="hour"
			y="weekday"
			value="orders"
			:min="0"
			:max="data?.max ?? 0"
			:format="formatCount"
			:loading="loading"
			:error="error"
		>
			<template #empty>
				<span class="text-p-sm text-ink-gray-5">
					No orders were placed in this period.
				</span>
			</template>
		</HeatmapChart>
	</ChartCard>
</template>
