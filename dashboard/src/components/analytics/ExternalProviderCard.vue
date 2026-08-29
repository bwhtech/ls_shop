<script setup lang="ts">
import { openSettings } from "@/components/settings"
import type { ProviderReadback } from "@/types"
import { formatCount } from "@/utils/format"
import { Alert, Button } from "frappe-ui"
import { AreaChart } from "frappe-ui/charts"
import { computed } from "vue"
import AnalyticsPanel from "./AnalyticsPanel.vue"

const props = defineProps<{
	title: string
	subtitle: string
	/** The summary key holding this provider's daily series - it does not match the provider name. */
	dailyField: "daily_sessions" | "daily_pageviews"
	dailyLabel: string
	notConnectedMessage: string
	readback: ProviderReadback | undefined
	loading?: boolean
	error?: string | null
}>()

const totals = computed(() =>
	Object.entries(props.readback?.summary?.totals ?? {}).slice(0, 4),
)

const daily = computed(() => {
	const series = props.readback?.summary?.[props.dailyField] ?? {}
	return Object.entries(series).map(([day, count]) => ({ day, count }))
})

/** A metric key arrives as the provider names it: `activeUsers`, `PageView`. */
function readableMetric(key: string) {
	return key.replace(/_/g, " ")
}

function openAnalyticsSettings() {
	openSettings("analytics")
}
</script>

<template>
	<AnalyticsPanel
		:title="title"
		:subtitle="subtitle"
		:loading="loading"
		:error="error"
		:skeleton-rows="3"
	>
		<div v-if="!readback?.configured" class="space-y-2 py-2">
			<p class="text-p-sm text-ink-gray-5">{{ notConnectedMessage }}</p>
			<Button
				variant="subtle"
				icon-left="lucide-plug"
				label="Set up tracking"
				@click="openAnalyticsSettings"
			/>
		</div>

		<div
			v-else-if="readback.error"
			class="rounded-4 border border-outline-amber-3 bg-surface-amber-2 px-3 py-2"
		>
			<p class="text-p-sm text-ink-amber-7">{{ readback.error }}</p>
		</div>

		<div v-else-if="totals.length" class="space-y-3">
			<div class="grid grid-cols-2 gap-2">
				<div v-for="[metric, count] in totals" :key="metric" class="min-w-0">
					<div class="truncate text-p-xs capitalize text-ink-gray-5">
						{{ readableMetric(metric) }}
					</div>
					<div class="text-base font-semibold text-ink-gray-8">
						{{ formatCount(Number(count)) }}
					</div>
				</div>
			</div>
			<div v-if="daily.length" class="h-32 w-full">
				<AreaChart
					:data="daily"
					x="day"
					y="count"
					:series-config="{ count: { label: dailyLabel } }"
					:y-axis="{ format: formatCount }"
				/>
			</div>
		</div>

		<p v-else class="py-4 text-p-sm text-ink-gray-5">No summary data yet.</p>
	</AnalyticsPanel>
</template>
