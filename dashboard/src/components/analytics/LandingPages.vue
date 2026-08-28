<script setup lang="ts">
import {
	useAnalyticsRange,
	useAnalyticsReport,
} from "@/composables/useAnalyticsRange"
import type { LandingPageRow } from "@/types"
import { computed } from "vue"
import AnalyticsPanel from "./AnalyticsPanel.vue"
import AnalyticsTable from "./AnalyticsTable.vue"
import {
	type AnalyticsTableColumn,
	countColumn,
	percentColumn,
} from "./columns"

const { rangeParams, rangeCaption } = useAnalyticsRange()

const columns: AnalyticsTableColumn<LandingPageRow>[] = [
	{ key: "path", label: "Landing page" },
	countColumn("sessions", "Sessions"),
	percentColumn("conversion_rate", "Conversion"),
]

const { data, loading, error } = useAnalyticsReport<LandingPageRow[]>(
	"get_landing_pages",
	() => ({ ...rangeParams.value, limit: 8 }),
)

const rows = computed(() => data.value ?? [])
</script>

<template>
	<AnalyticsPanel
		title="Landing pages"
		:subtitle="`Where sessions start · ${rangeCaption}`"
		:loading="loading"
		:error="error"
		:empty="!rows.length"
		empty-message="No landing pages were tracked in this period."
	>
		<AnalyticsTable :columns="columns" :rows="rows" row-key="path" />
	</AnalyticsPanel>
</template>
