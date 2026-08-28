<script setup lang="ts">
import {
	onAnalyticsRefresh,
	useAnalyticsRange,
} from "@/composables/useAnalyticsRange"
import type { AnalyticsRangeParams, LandingPageRow } from "@/types"
import { formatCount, formatPercent } from "@/utils/format"
import { useCall } from "frappe-ui"
import { computed } from "vue"
import AnalyticsPanel from "./AnalyticsPanel.vue"
import AnalyticsTable from "./AnalyticsTable.vue"
import type { AnalyticsTableColumn } from "./AnalyticsTable.vue"

const { rangeParams, rangeCaption } = useAnalyticsRange()

const columns: AnalyticsTableColumn[] = [
	{ key: "path", label: "Landing page" },
	{ key: "sessions", label: "Sessions", numeric: true },
	{ key: "conversion_rate", label: "Conversion", numeric: true },
]

const landingPages = useCall<
	LandingPageRow[],
	AnalyticsRangeParams & { limit: number }
>({
	url: "/api/v2/method/ls_shop.api.analytics_dashboard.get_landing_pages",
	params: () => ({ ...rangeParams.value, limit: 8 }),
	refetch: true,
})

onAnalyticsRefresh(() => landingPages.reload())

const rows = computed(() => landingPages.data ?? [])
</script>

<template>
	<AnalyticsPanel
		title="Landing pages"
		:subtitle="`Where sessions start · ${rangeCaption}`"
		:loading="landingPages.loading && !landingPages.data"
		:error="landingPages.error?.message ?? null"
		:empty="!rows.length"
		empty-message="No landing pages were tracked in this period."
	>
		<AnalyticsTable :columns="columns" :rows="rows" row-key="path">
			<template #sessions="{ row }">
				{{ formatCount(Number(row.sessions)) }}
			</template>
			<template #conversion_rate="{ row }">
				{{ formatPercent(Number(row.conversion_rate)) }}
			</template>
		</AnalyticsTable>
	</AnalyticsPanel>
</template>
