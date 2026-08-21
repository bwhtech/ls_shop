<script setup lang="ts">
import {
	onAnalyticsRefresh,
	useAnalyticsRange,
} from "@/composables/useAnalyticsRange"
import type { FunnelReport } from "@/types"
import { formatCount } from "@/utils/format"
import { TabButtons, useCall } from "frappe-ui"
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

const funnel = useCall<FunnelReport>({
	url: "/api/v2/method/ls_shop.api.analytics_dashboard.get_funnel",
	params: () => ({ ...rangeParams.value, device: device.value }),
	refetch: true,
})

onAnalyticsRefresh(() => funnel.reload())

// Every stage is a share of the first one, so a funnel with no sessions has nothing to divide by.
const stages = computed(() => {
	const rows = funnel.data?.stages ?? []
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
			:loading="funnel.loading && !funnel.data"
			:error="funnel.error?.message ?? null"
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
