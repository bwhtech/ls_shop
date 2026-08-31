<script setup lang="ts">
import {
	useAnalyticsRange,
	useAnalyticsReport,
} from "@/composables/useAnalyticsRange"
import type { StockMovement } from "@/types"
import { formatCount, formatDate } from "@/utils/format"
import { ChartCard, LineChart } from "frappe-ui/charts"
import { computed } from "vue"

const { rangeCaption } = useAnalyticsRange()

const { data, loading, error } =
	useAnalyticsReport<StockMovement>("get_stock_movement")

const rows = computed(() => {
	const movement = data.value
	if (!movement?.warehouse) return []
	return movement.labels.map((day, index) => ({
		day,
		units_in: movement.units_in[index],
		units_out: movement.units_out[index],
		on_hand: movement.on_hand[index],
	}))
})

const subtitle = computed(() =>
	data.value?.warehouse
		? `Units in and out of ${data.value.warehouse} · ${rangeCaption.value}`
		: "No shop warehouse is set, so stock cannot be reported",
)
</script>

<template>
	<ChartCard class="h-80">
		<LineChart
			title="Stock over time"
			:subtitle="subtitle"
			:data="rows"
			x="day"
			:y="['on_hand', 'units_in', 'units_out']"
			:x-axis="{ format: formatDate }"
			:y-axis="{ title: 'On hand', format: formatCount }"
			:y2-axis="{ title: 'Movement', format: formatCount }"
			:series-config="{
				on_hand: { label: 'On hand', type: 'area' },
				units_in: { label: 'Units in', axis: 'y2' },
				units_out: { label: 'Units out', axis: 'y2' },
			}"
			:loading="loading"
			:error="error"
		>
			<template #empty>
				<span class="text-p-sm text-ink-gray-5">
					No stock moved in this period.
				</span>
			</template>
		</LineChart>
	</ChartCard>
</template>
