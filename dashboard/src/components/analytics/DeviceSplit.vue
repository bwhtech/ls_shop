<script setup lang="ts">
import {
	onAnalyticsRefresh,
	useAnalyticsRange,
} from "@/composables/useAnalyticsRange"
import type { AnalyticsRangeParams, DeviceSplitRow } from "@/types"
import { formatCount, formatPercent } from "@/utils/format"
import { useCall } from "frappe-ui"
import { DonutChart } from "frappe-ui/charts"
import { computed } from "vue"
import AnalyticsPanel from "./AnalyticsPanel.vue"
import AnalyticsTable from "./AnalyticsTable.vue"
import type { AnalyticsTableColumn } from "./AnalyticsTable.vue"

const { rangeParams, rangeCaption } = useAnalyticsRange()

const columns: AnalyticsTableColumn[] = [
	{ key: "device", label: "Device" },
	{ key: "sessions", label: "Sessions", numeric: true },
	{ key: "conversion_rate", label: "Conversion", numeric: true },
]

const deviceSplit = useCall<DeviceSplitRow[], AnalyticsRangeParams>({
	url: "/api/v2/method/ls_shop.api.analytics_dashboard.get_device_split",
	params: () => rangeParams.value,
	refetch: true,
})

onAnalyticsRefresh(() => deviceSplit.reload())

const rows = computed(() => deviceSplit.data ?? [])
</script>

<!--
	The ring answers "how do they arrive", the table under it "and do they buy" - a conversion
	rate is not a share of a total, so it cannot go in the ring.
-->
<template>
	<AnalyticsPanel
		title="Devices"
		:subtitle="`Sessions and conversion by device · ${rangeCaption}`"
		:loading="deviceSplit.loading && !deviceSplit.data"
		:error="deviceSplit.error?.message ?? null"
		:empty="!rows.length"
		empty-message="No sessions were recorded in this period."
	>
		<div class="space-y-3">
			<div class="h-56 w-full">
				<DonutChart
					:data="rows"
					category="device"
					value="sessions"
					center-label="sessions"
					:format="formatCount"
				/>
			</div>
			<AnalyticsTable :columns="columns" :rows="rows" row-key="device">
				<template #sessions="{ row }">
					{{ formatCount(Number(row.sessions)) }}
				</template>
				<template #conversion_rate="{ row }">
					{{ formatPercent(Number(row.conversion_rate)) }}
				</template>
			</AnalyticsTable>
		</div>
	</AnalyticsPanel>
</template>
