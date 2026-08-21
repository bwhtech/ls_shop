<script setup lang="ts">
import AbandonedCarts from "@/components/analytics/AbandonedCarts.vue"
import ConversionFunnel from "@/components/analytics/ConversionFunnel.vue"
import DeviceSplit from "@/components/analytics/DeviceSplit.vue"
import ExternalProviderCard from "@/components/analytics/ExternalProviderCard.vue"
import ItemAnalyticsDialog from "@/components/analytics/ItemAnalyticsDialog.vue"
import KpiTiles from "@/components/analytics/KpiTiles.vue"
import LandingPages from "@/components/analytics/LandingPages.vue"
import LiveViewCard from "@/components/analytics/LiveViewCard.vue"
import ProductEngagement from "@/components/analytics/ProductEngagement.vue"
import SalesHeatmap from "@/components/analytics/SalesHeatmap.vue"
import SalesOverTime from "@/components/analytics/SalesOverTime.vue"
import TopProducts from "@/components/analytics/TopProducts.vue"
import TrackingHealthCard from "@/components/analytics/TrackingHealthCard.vue"
import TrafficSources from "@/components/analytics/TrafficSources.vue"
import {
	analyticsRangeOptions,
	onAnalyticsRefresh,
	refreshAnalytics,
	useAnalyticsRange,
} from "@/composables/useAnalyticsRange"
import type { AnalyticsOverview, ExternalSummaries } from "@/types"
import {
	Button,
	PageHeader,
	PageHeaderTitle,
	ScrollArea,
	TabButtons,
	useCall,
} from "frappe-ui"
import { computed, ref } from "vue"

const { preset, rangeParams } = useAnalyticsRange()

// The overview owns the store currency, so every money figure on the page reads it from here
// rather than each widget asking the server for the same string.
const overview = useCall<AnalyticsOverview>({
	url: "/api/v2/method/ls_shop.api.analytics_dashboard.get_overview",
	params: () => rangeParams.value,
	refetch: true,
})

// One read-back for both provider cards: the endpoint returns GA4 and Meta together.
const externalSummaries = useCall<ExternalSummaries>({
	url: "/api/v2/method/ls_shop.api.analytics_dashboard.get_external_summaries",
})

onAnalyticsRefresh(() => {
	overview.reload()
	externalSummaries.reload()
})

const currency = computed(() => overview.data?.currency ?? "")

const drilldownItemCode = ref<string | null>(null)
const showDrilldown = ref(false)

function openProductDrilldown(itemCode: string) {
	drilldownItemCode.value = itemCode
	showDrilldown.value = true
}
</script>

<template>
	<div class="flex h-full flex-col bg-surface-base">
		<PageHeader>
			<PageHeaderTitle>Analytics</PageHeaderTitle>
			<div class="flex items-center gap-2">
				<TabButtons v-model="preset" :options="analyticsRangeOptions" />
				<Button
					variant="ghost"
					icon-left="lucide-refresh-cw"
					label="Refresh"
					:loading="overview.loading"
					@click="refreshAnalytics"
				/>
			</div>
		</PageHeader>

		<ScrollArea class="min-h-0 flex-1" viewport-class="pb-40">
			<!-- Section order follows the Desk dashboard: what is happening now, then the period's
			     numbers, then the journey, then the catalogue, then acquisition, then diagnostics. -->
			<div class="mx-auto max-w-6xl space-y-4 px-3 pt-5 sm:px-5">
				<LiveViewCard :currency="currency" />

				<KpiTiles
					:overview="overview.data"
					:currency="currency"
					:loading="overview.loading && !overview.data"
					:error="overview.error?.message ?? null"
				/>

				<SalesOverTime :currency="currency" />

				<ConversionFunnel />

				<div class="grid grid-cols-1 gap-4 xl:grid-cols-2">
					<TopProducts :currency="currency" @select="openProductDrilldown" />
					<ProductEngagement @select="openProductDrilldown" />
				</div>

				<div class="grid grid-cols-1 gap-4 xl:grid-cols-2">
					<TrafficSources :currency="currency" />
					<div class="space-y-4">
						<DeviceSplit />
						<LandingPages />
					</div>
				</div>

				<AbandonedCarts :currency="currency" />

				<SalesHeatmap />

				<div class="grid grid-cols-1 gap-4 lg:grid-cols-3">
					<ExternalProviderCard
						title="Google Analytics 4"
						subtitle="Last 30 days, from the GA4 API"
						daily-field="daily_sessions"
						daily-label="Daily sessions"
						not-connected-message="GA4 is not connected."
						:readback="externalSummaries.data?.ga4"
						:loading="externalSummaries.loading && !externalSummaries.data"
						:error="externalSummaries.error?.message ?? null"
					/>
					<ExternalProviderCard
						title="Meta Pixel"
						subtitle="Last 30 days, from the Meta API"
						daily-field="daily_pageviews"
						daily-label="Daily pageviews"
						not-connected-message="The Meta Pixel is not connected."
						:readback="externalSummaries.data?.meta"
						:loading="externalSummaries.loading && !externalSummaries.data"
						:error="externalSummaries.error?.message ?? null"
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
