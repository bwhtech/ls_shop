<script setup lang="ts">
import { useAnalyticsReport } from "@/composables/useAnalyticsRange"
import type { LiveView } from "@/types"
import { formatCount, formatMoney } from "@/utils/format"
import { useIntervalFn } from "@vueuse/core"
import { NumberCard } from "frappe-ui/charts"
import { computed } from "vue"
import AnalyticsPanel from "./AnalyticsPanel.vue"

const props = defineProps<{ currency: string }>()

const REFRESH_INTERVAL_MS = 30000

const { data, loading, error, reload } = useAnalyticsReport<LiveView>(
	"get_live_view",
	() => ({}),
)

useIntervalFn(reload, REFRESH_INTERVAL_MS)

const tiles = computed(() => {
	const live = data.value
	if (!live) return []
	return [
		{ title: "Visitors now", value: formatCount(live.visitors_now) },
		{ title: "Active carts", value: formatCount(live.active_carts) },
		{ title: "Checking out", value: formatCount(live.checking_out) },
		{ title: "Sessions today", value: formatCount(live.today.sessions) },
		{ title: "Orders today", value: formatCount(live.today.orders) },
		{
			title: "Sales today",
			value: formatMoney(live.today.sales, props.currency),
		},
	]
})
</script>

<template>
	<AnalyticsPanel
		title="Live view"
		subtitle="Right now on your store · updates every 30s"
		:loading="loading"
		:error="error"
		:empty="!tiles.length"
		empty-message="Nothing has happened on the store yet."
		:skeleton-rows="2"
	>
		<div class="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-6">
			<NumberCard
				v-for="tile in tiles"
				:key="tile.title"
				:title="tile.title"
				:value="tile.value"
				:card="false"
			/>
		</div>
	</AnalyticsPanel>
</template>
