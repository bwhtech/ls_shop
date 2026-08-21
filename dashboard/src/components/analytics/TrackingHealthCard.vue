<script setup lang="ts">
import { openSettings } from "@/components/settings"
import { onAnalyticsRefresh } from "@/composables/useAnalyticsRange"
import type { BadgeTheme, ProviderHealth, TrackingHealth } from "@/types"
import { formatCount } from "@/utils/format"
import { Badge, Button, useCall } from "frappe-ui"
import { computed } from "vue"
import AnalyticsPanel from "./AnalyticsPanel.vue"
import AnalyticsTable from "./AnalyticsTable.vue"
import type { AnalyticsTableColumn } from "./AnalyticsTable.vue"

const columns: AnalyticsTableColumn[] = [
	{ key: "source", label: "Source" },
	{ key: "purchases", label: "Purchases (30d)", numeric: true },
	{ key: "status", label: "Status" },
]

const health = useCall<TrackingHealth>({
	url: "/api/v2/method/ls_shop.api.analytics_dashboard.get_tracking_health",
})

onAnalyticsRefresh(() => health.reload())

/** Off is a choice and Error is a fault - a store owner has to be able to tell them apart. */
function providerRow(label: string, provider: ProviderHealth | undefined) {
	if (!provider?.configured) {
		return {
			source: label,
			purchases: "—",
			status: "Off",
			theme: "gray" as BadgeTheme,
		}
	}
	if (!provider.ok) {
		return {
			source: label,
			purchases: "—",
			status: "Error",
			theme: "red" as BadgeTheme,
		}
	}
	return {
		source: label,
		purchases: formatCount(provider.purchases_30d ?? 0),
		status: "OK",
		theme: "green" as BadgeTheme,
	}
}

const rows = computed(() => {
	const data = health.data
	if (!data) return []
	return [
		{
			source: "First-party",
			purchases: formatCount(data.first_party.purchases_30d),
			status: "Active",
			theme: "green" as BadgeTheme,
		},
		providerRow("GA4", data.ga4),
		providerRow("Meta Pixel", data.meta),
	]
})

// Off and Error both end at the same place - the credentials screen.
const needsAttention = computed(() => {
	const data = health.data
	if (!data) return false
	return [data.ga4, data.meta].some(
		(provider) => !provider?.configured || !provider.ok,
	)
})

const warnings = computed(() =>
	[health.data?.ga4?.error, health.data?.meta?.error].filter(
		(error): error is string => Boolean(error),
	),
)
</script>

<template>
	<AnalyticsPanel
		title="Tracking health"
		subtitle="Do all your trackers agree?"
		:loading="health.loading && !health.data"
		:error="health.error?.message ?? null"
		:empty="!rows.length"
		empty-message="No tracking data yet."
		:skeleton-rows="3"
	>
		<div class="space-y-3">
			<p class="text-p-sm text-ink-gray-5">
				<span class="font-semibold text-ink-gray-8">
					{{ formatCount(health.data?.first_party.events_24h ?? 0) }}
				</span>
				first-party events · 24h
			</p>

			<AnalyticsTable :columns="columns" :rows="rows" row-key="source">
				<template #status="{ row }">
					<Badge
						:theme="row.theme as BadgeTheme"
						variant="subtle"
						:label="String(row.status)"
					/>
				</template>
			</AnalyticsTable>

			<p
				v-for="warning in warnings"
				:key="warning"
				class="rounded-4 border border-outline-amber-3 bg-surface-amber-2 px-3 py-2 text-p-sm text-ink-amber-7"
			>
				{{ warning }}
			</p>

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
