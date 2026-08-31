<script setup lang="ts">
import AnalyticsHeader from "@/components/analytics/AnalyticsHeader.vue"
import DeviceSplit from "@/components/analytics/DeviceSplit.vue"
import ExternalProviderCard from "@/components/analytics/ExternalProviderCard.vue"
import ItemAnalyticsDialog from "@/components/analytics/ItemAnalyticsDialog.vue"
import KpiTiles from "@/components/analytics/KpiTiles.vue"
import LandingPages from "@/components/analytics/LandingPages.vue"
import LiveViewCard from "@/components/analytics/LiveViewCard.vue"
import ProductEngagement from "@/components/analytics/ProductEngagement.vue"
import TrackingHealthCard from "@/components/analytics/TrackingHealthCard.vue"
import TrafficSources from "@/components/analytics/TrafficSources.vue"
import {
	analyticsRangeOptions,
	onAnalyticsRefresh,
	refreshAnalytics,
	useAnalyticsRange,
} from "@/composables/useAnalyticsRange"
import type {
	AnalyticsKpiKey,
	AnalyticsOverview,
	AnalyticsRangeParams,
	ExternalSummaries,
} from "@/types"
import { errorMessage } from "@/utils/errors"
import { Button, ScrollArea, TabButtons, useCall } from "frappe-ui"
import { computed, ref } from "vue"

const { preset, rangeParams } = useAnalyticsRange()

const overview = useCall<AnalyticsOverview, AnalyticsRangeParams>({
	url: "/api/v2/method/ls_shop.api.analytics_dashboard.get_overview",
	params: () => rangeParams.value,
	refetch: true,
})

const externalSummaries = useCall<ExternalSummaries>({
	url: "/api/v2/method/ls_shop.api.analytics_dashboard.get_external_summaries",
})

onAnalyticsRefresh(() => {
	overview.reload()
	externalSummaries.reload()
})

const currency = computed(() => overview.data?.currency ?? "")

// Traffic and how well it converts; the money it made is the sales tile.
const websiteKpis: AnalyticsKpiKey[] = ["sessions", "conversion_rate"]

const drilldownItemCode = ref<string | null>(null)
const showDrilldown = ref(false)

function openProductDrilldown(itemCode: string) {
	drilldownItemCode.value = itemCode
	showDrilldown.value = true
}
</script>

<template>
	<div class="flex h-full flex-col bg-surface-base">
		<AnalyticsHeader>
			<template #actions>
				<TabButtons v-model="preset" :options="analyticsRangeOptions" />
				<Button
					variant="ghost"
					icon-left="lucide-refresh-cw"
					label="Refresh"
					:loading="overview.loading"
					@click="refreshAnalytics"
				/>
			</template>
		</AnalyticsHeader>

		<ScrollArea class="min-h-0 flex-1" viewport-class="pb-40">
			<div class="mx-auto max-w-6xl space-y-4 px-3 pt-5 sm:px-5">
				<LiveViewCard :currency="currency" />

				<KpiTiles
					:overview="overview.data"
					:currency="currency"
					:keys="websiteKpis"
					:loading="overview.loading && !overview.data"
					:error="overview.error ? errorMessage(overview.error) : null"
				/>

				<TrafficSources :currency="currency" />

				<div class="grid grid-cols-1 gap-4 xl:grid-cols-2">
					<DeviceSplit />
					<LandingPages />
				</div>

				<ProductEngagement @select="openProductDrilldown" />

				<div class="grid grid-cols-1 gap-4 lg:grid-cols-3">
					<ExternalProviderCard
						title="Google Analytics 4"
						subtitle="Last 30 days, from the GA4 API"
						daily-field="daily_sessions"
						daily-label="Daily sessions"
						not-connected-message="GA4 is not connected."
						:readback="externalSummaries.data?.ga4"
						:loading="externalSummaries.loading && !externalSummaries.data"
						:error="externalSummaries.error ? errorMessage(externalSummaries.error) : null"
					/>
					<ExternalProviderCard
						title="Meta Pixel"
						subtitle="Last 30 days, from the Meta API"
						daily-field="daily_pageviews"
						daily-label="Daily pageviews"
						not-connected-message="The Meta Pixel is not connected."
						:readback="externalSummaries.data?.meta"
						:loading="externalSummaries.loading && !externalSummaries.data"
						:error="externalSummaries.error ? errorMessage(externalSummaries.error) : null"
					/>
					<TrackingHealthCard />
				</div>
			</div>
		</ScrollArea>

		<ItemAnalyticsDialog
			v-model:open="showDrilldown"
			:item-code="drilldownItemCode"
			:currency="currency"
		/>
	</div>
</template>
