<script setup lang="ts">
import {
	onAnalyticsRefresh,
	useAnalyticsRange,
} from "@/composables/useAnalyticsRange"
import type { AnalyticsRangeParams, TrafficSourceRow } from "@/types"
import { formatCount, formatMoney, formatPercent } from "@/utils/format"
import { useCall } from "frappe-ui"
import { computed } from "vue"
import AnalyticsPanel from "./AnalyticsPanel.vue"
import AnalyticsTable from "./AnalyticsTable.vue"
import type { AnalyticsTableColumn } from "./AnalyticsTable.vue"

const props = defineProps<{ currency: string }>()

const { rangeParams, rangeCaption } = useAnalyticsRange()

const columns: AnalyticsTableColumn[] = [
	{ key: "source", label: "Source" },
	{ key: "campaign", label: "Campaign" },
	{ key: "sessions", label: "Sessions", numeric: true },
	{ key: "orders", label: "Orders", numeric: true },
	{ key: "revenue", label: "Revenue", numeric: true },
	{ key: "conversion_rate", label: "Conversion", numeric: true },
]

const trafficSources = useCall<TrafficSourceRow[], AnalyticsRangeParams>({
	url: "/api/v2/method/ls_shop.api.analytics_dashboard.get_traffic_sources",
	params: () => rangeParams.value,
	refetch: true,
})

onAnalyticsRefresh(() => trafficSources.reload())

// source, medium and campaign are one group server-side, so they are one identity here too.
const rows = computed(() =>
	(trafficSources.data ?? []).map((row) => ({
		...row,
		group: row.medium ? `${row.source} / ${row.medium}` : row.source,
		key: `${row.source} / ${row.medium} / ${row.campaign}`,
	})),
)
</script>

<template>
	<AnalyticsPanel
		title="Traffic sources"
		:subtitle="`Where sessions and revenue come from · ${rangeCaption}`"
		:loading="trafficSources.loading && !trafficSources.data"
		:error="trafficSources.error?.message ?? null"
		:empty="!rows.length"
		empty-message="No traffic was attributed in this period."
	>
		<AnalyticsTable :columns="columns" :rows="rows" row-key="key">
			<template #source="{ row }">{{ row.group }}</template>
			<template #campaign="{ row }">
				<span v-if="row.campaign" class="text-ink-gray-8">{{ row.campaign }}</span>
				<span v-else class="text-ink-gray-4">&mdash;</span>
			</template>
			<template #sessions="{ row }">
				{{ formatCount(Number(row.sessions)) }}
			</template>
			<template #orders="{ row }">{{ formatCount(Number(row.orders)) }}</template>
			<template #revenue="{ row }">
				{{ formatMoney(Number(row.revenue), props.currency) }}
			</template>
			<template #conversion_rate="{ row }">
				{{ formatPercent(Number(row.conversion_rate)) }}
			</template>
		</AnalyticsTable>
	</AnalyticsPanel>
</template>
