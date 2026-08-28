<script setup lang="ts">
import { openSettings } from "@/components/settings"
import { useAnalyticsReport } from "@/composables/useAnalyticsRange"
import type { BadgeTheme, ProviderHealth, TrackingHealth } from "@/types"
import { formatCount } from "@/utils/format"
import { Alert, Badge, Button } from "frappe-ui"
import { computed } from "vue"
import AnalyticsPanel from "./AnalyticsPanel.vue"
import AnalyticsTable from "./AnalyticsTable.vue"
import type { AnalyticsTableColumn } from "./columns"

type ProviderRow = {
	source: string
	purchases: string
	status: string
	theme: BadgeTheme
}

const columns: AnalyticsTableColumn<ProviderRow>[] = [
	{ key: "source", label: "Source" },
	{ key: "purchases", label: "Purchases (30d)", numeric: true },
	{ key: "status", label: "Status" },
]

// No params: the endpoint reports a fixed 30-day health window of its own.
const { data, loading, error } = useAnalyticsReport<TrackingHealth>(
	"get_tracking_health",
	() => ({}),
)

/** Off is a choice and Error is a fault - a store owner has to be able to tell them apart. */
function providerRow(
	label: string,
	provider: ProviderHealth | undefined,
): ProviderRow {
	if (!provider?.configured) {
		return { source: label, purchases: "—", status: "Off", theme: "gray" }
	}
	if (!provider.ok) {
		return { source: label, purchases: "—", status: "Error", theme: "red" }
	}
	return {
		source: label,
		purchases: formatCount(provider.purchases_30d ?? 0),
		status: "OK",
		theme: "green",
	}
}

const rows = computed<ProviderRow[]>(() => {
	const health = data.value
	if (!health) return []
	return [
		{
			source: "First-party",
			purchases: formatCount(health.first_party.purchases_30d),
			status: "Active",
			theme: "green",
		},
		providerRow("GA4", health.ga4),
		providerRow("Meta Pixel", health.meta),
	]
})

// Off and Error both end at the same place - the credentials screen.
const needsAttention = computed(() => {
	const health = data.value
	if (!health) return false
	return [health.ga4, health.meta].some(
		(provider) => !provider?.configured || !provider.ok,
	)
})

const warnings = computed(() =>
	[data.value?.ga4?.error, data.value?.meta?.error].filter(
		(message): message is string => Boolean(message),
	),
)
</script>

<template>
	<AnalyticsPanel
		title="Tracking health"
		subtitle="Do all your trackers agree?"
		:loading="loading"
		:error="error"
		:empty="!rows.length"
		empty-message="No tracking data yet."
		:skeleton-rows="3"
	>
		<div class="space-y-3">
			<p class="text-p-sm text-ink-gray-5">
				<span class="font-semibold text-ink-gray-8">
					{{ formatCount(data?.first_party.events_24h ?? 0) }}
				</span>
				first-party events · 24h
			</p>

			<AnalyticsTable :columns="columns" :rows="rows" row-key="source">
				<template #status="{ row }">
					<Badge :theme="row.theme" variant="subtle" :label="row.status" />
				</template>
			</AnalyticsTable>

			<Alert
				v-for="warning in warnings"
				:key="warning"
				theme="amber"
				:description="warning"
			/>

			<Button
				v-if="needsAttention"
				variant="subtle"
				icon-left="lucide-plug"
				label="Manage tracking settings"
				@click="openSettings('analytics')"
			/>
		</div>
	</AnalyticsPanel>
</template>
