<script setup lang="ts">
import type { LiveView } from "@/types"
import { formatCount, formatMoney } from "@/utils/format"
import { useCall } from "frappe-ui"
import { computed, onBeforeUnmount, onMounted } from "vue"
import AnalyticsPanel from "./AnalyticsPanel.vue"
import StatChip from "./StatChip.vue"

const props = defineProps<{ currency: string }>()

const REFRESH_INTERVAL_MS = 30000

const liveView = useCall<LiveView>({
	url: "/api/v2/method/ls_shop.api.analytics_dashboard.get_live_view",
})

let refreshTimer: ReturnType<typeof setInterval> | undefined

onMounted(() => {
	refreshTimer = setInterval(() => liveView.reload(), REFRESH_INTERVAL_MS)
})

onBeforeUnmount(() => {
	if (refreshTimer) clearInterval(refreshTimer)
})

const chips = computed(() => {
	const data = liveView.data
	if (!data) return []
	return [
		{ label: "Visitors now", value: formatCount(data.visitors_now) },
		{ label: "Active carts", value: formatCount(data.active_carts) },
		{ label: "Checking out", value: formatCount(data.checking_out) },
		{ label: "Sessions today", value: formatCount(data.today.sessions) },
		{ label: "Orders today", value: formatCount(data.today.orders) },
		{
			label: "Sales today",
			value: formatMoney(data.today.sales, props.currency),
		},
	]
})
</script>

<template>
	<AnalyticsPanel
		title="Live view"
		subtitle="Right now on your store · updates every 30s"
		:loading="liveView.loading && !liveView.data"
		:error="liveView.error?.message ?? null"
		:empty="!chips.length"
		empty-message="Nothing has happened on the store yet."
		:skeleton-rows="2"
	>
		<div class="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-6">
			<StatChip
				v-for="chip in chips"
				:key="chip.label"
				:label="chip.label"
				:value="chip.value"
			/>
		</div>
	</AnalyticsPanel>
</template>
