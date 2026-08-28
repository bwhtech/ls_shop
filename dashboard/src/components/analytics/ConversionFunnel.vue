<script setup lang="ts">
import {
	useAnalyticsRange,
	useAnalyticsReport,
} from "@/composables/useAnalyticsRange"
import type { FunnelReport } from "@/types"
import { formatCount } from "@/utils/format"
import { TabButtons } from "frappe-ui"
import { ChartCard, FunnelChart } from "frappe-ui/charts"
import { computed, ref } from "vue"

const { rangeParams, rangeCaption } = useAnalyticsRange()

const device = ref("")

const deviceOptions = [
	{ label: "All", value: "" },
	{ label: "Desktop", value: "desktop" },
	{ label: "Mobile", value: "mobile" },
	{ label: "Tablet", value: "tablet" },
]

const { data, loading, error } = useAnalyticsReport<FunnelReport>(
	"get_funnel",
	() => ({ ...rangeParams.value, device: device.value }),
)

// Every stage is a share of the first one, so a funnel with no sessions has nothing to divide by.
const stages = computed(() => {
	const rows = data.value?.stages ?? []
	return rows[0]?.count ? rows : []
})
</script>

<template>
	<ChartCard class="h-96">
		<FunnelChart
			title="Conversion funnel"
			:subtitle="`From session to purchase · ${rangeCaption}`"
			:data="stages"
			category="label"
			value="count"
			:format="formatCount"
			:loading="loading"
			:error="error"
		>
			<template #actions>
				<TabButtons v-model="device" :options="deviceOptions" />
			</template>
			<template #empty>
				<span class="text-p-sm text-ink-gray-5">
					No sessions were recorded in this period.
				</span>
			</template>
		</FunnelChart>
	</ChartCard>
</template>
