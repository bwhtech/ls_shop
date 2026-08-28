<script setup lang="ts">
import {
	useAnalyticsRange,
	useAnalyticsReport,
} from "@/composables/useAnalyticsRange"
import type { DeviceSplitRow } from "@/types"
import { formatCount } from "@/utils/format"
import { DonutChart } from "frappe-ui/charts"
import { computed } from "vue"
import AnalyticsPanel from "./AnalyticsPanel.vue"
import AnalyticsTable from "./AnalyticsTable.vue"
import {
	type AnalyticsTableColumn,
	countColumn,
	percentColumn,
} from "./columns"

const { rangeCaption } = useAnalyticsRange()

const columns: AnalyticsTableColumn<DeviceSplitRow>[] = [
	{ key: "device", label: "Device" },
	countColumn("sessions", "Sessions"),
	percentColumn("conversion_rate", "Conversion"),
]

const { data, loading, error } =
	useAnalyticsReport<DeviceSplitRow[]>("get_device_split")

const rows = computed(() => data.value ?? [])
</script>

<!--
	The ring answers "how do they arrive", the table under it "and do they buy" - a conversion
	rate is not a share of a total, so it cannot go in the ring.
-->
<template>
	<AnalyticsPanel
		title="Devices"
		:subtitle="`Sessions and conversion by device · ${rangeCaption}`"
		:loading="loading"
		:error="error"
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
			<AnalyticsTable :columns="columns" :rows="rows" row-key="device" />
		</div>
	</AnalyticsPanel>
</template>
