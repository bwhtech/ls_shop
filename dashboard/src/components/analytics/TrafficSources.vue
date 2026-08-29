<script setup lang="ts">
import {
	useAnalyticsRange,
	useAnalyticsReport,
} from "@/composables/useAnalyticsRange"
import type { TrafficSourceRow } from "@/types"
import { computed } from "vue"
import AnalyticsPanel from "./AnalyticsPanel.vue"
import AnalyticsTable from "./AnalyticsTable.vue"
import {
	type AnalyticsTableColumn,
	countColumn,
	moneyColumn,
	percentColumn,
} from "./columns"

const props = defineProps<{ currency: string }>()

const { rangeCaption } = useAnalyticsRange()

type TrafficSourceGroupRow = TrafficSourceRow & { group: string; key: string }

const columns: AnalyticsTableColumn<TrafficSourceGroupRow>[] = [
	{ key: "group", label: "Source" },
	{ key: "campaign", label: "Campaign" },
	countColumn("sessions", "Sessions"),
	countColumn("orders", "Orders"),
	moneyColumn("revenue", "Revenue", () => props.currency),
	percentColumn("conversion_rate", "Conversion"),
]

const { data, loading, error } = useAnalyticsReport<TrafficSourceRow[]>(
	"get_traffic_sources",
)

const rows = computed<TrafficSourceGroupRow[]>(() =>
	(data.value ?? []).map((row) => ({
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
		:loading="loading"
		:error="error"
		:empty="!rows.length"
		empty-message="No traffic was attributed in this period."
	>
		<AnalyticsTable :columns="columns" :rows="rows" row-key="key">
			<template #campaign="{ row }">
				<span v-if="row.campaign" class="text-ink-gray-8">{{ row.campaign }}</span>
				<span v-else class="text-ink-gray-4">&mdash;</span>
			</template>
		</AnalyticsTable>
	</AnalyticsPanel>
</template>
