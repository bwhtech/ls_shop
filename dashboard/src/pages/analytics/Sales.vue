<script setup lang="ts">
import AbandonedCarts from "@/components/analytics/AbandonedCarts.vue"
import AnalyticsHeader from "@/components/analytics/AnalyticsHeader.vue"
import ConversionFunnel from "@/components/analytics/ConversionFunnel.vue"
import ItemAnalyticsDialog from "@/components/analytics/ItemAnalyticsDialog.vue"
import KpiTiles from "@/components/analytics/KpiTiles.vue"
import SalesHeatmap from "@/components/analytics/SalesHeatmap.vue"
import SalesOverTime from "@/components/analytics/SalesOverTime.vue"
import TopProducts from "@/components/analytics/TopProducts.vue"
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

onAnalyticsRefresh(() => overview.reload())

const currency = computed(() => overview.data?.currency ?? "")

// What was sold and what it earned; how many visitors it took to get there is the website's tile.
const salesKpis: AnalyticsKpiKey[] = [
	"total_sales",
	"orders",
	"aov",
	"conversion_rate",
	"returning_customer_rate",
]

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
				<KpiTiles
					:overview="overview.data"
					:currency="currency"
					:keys="salesKpis"
					:loading="overview.loading && !overview.data"
					:error="overview.error ? errorMessage(overview.error) : null"
				/>

				<SalesOverTime :currency="currency" />

				<ConversionFunnel />

				<TopProducts :currency="currency" @select="openProductDrilldown" />

				<AbandonedCarts :currency="currency" />

				<SalesHeatmap />
			</div>
		</ScrollArea>

		<ItemAnalyticsDialog
			v-model:open="showDrilldown"
			:item-code="drilldownItemCode"
			:currency="currency"
		/>
	</div>
</template>
