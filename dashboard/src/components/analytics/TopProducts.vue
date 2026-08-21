<script setup lang="ts">
import {
	onAnalyticsRefresh,
	useAnalyticsRange,
} from "@/composables/useAnalyticsRange"
import type { TopProduct } from "@/types"
import { formatCount, formatMoney } from "@/utils/format"
import { TabButtons, useCall } from "frappe-ui"
import { BarChart, ChartCard } from "frappe-ui/charts"
import type { ChartDatapointEvent } from "frappe-ui/charts"
import { computed, ref } from "vue"

const props = defineProps<{ currency: string }>()
const emit = defineEmits<{ select: [itemCode: string] }>()

const { rangeParams, rangeCaption } = useAnalyticsRange()

const sortBy = ref<"revenue" | "units">("revenue")

const sortOptions = [
	{ label: "Revenue", value: "revenue" },
	{ label: "Units", value: "units" },
]

const topProducts = useCall<TopProduct[]>({
	url: "/api/v2/method/ls_shop.api.analytics_dashboard.get_top_products",
	params: () => ({ ...rangeParams.value, sort_by: sortBy.value, limit: 10 }),
	refetch: true,
})

onAnalyticsRefresh(() => topProducts.reload())

// Horizontal bars run bottom-up, so the best seller has to go last to sit at the top.
const rows = computed(() => [...(topProducts.data ?? [])].reverse())

const formatValue = computed(() =>
	sortBy.value === "revenue"
		? (value: number) => formatMoney(value, props.currency, true)
		: formatCount,
)

function openProduct(event: ChartDatapointEvent) {
	const itemCode = event.row?.item_code
	if (itemCode) emit("select", String(itemCode))
}
</script>

<template>
	<ChartCard class="h-96">
		<BarChart
			title="Top products"
			:subtitle="`Best sellers · ${rangeCaption}`"
			:data="rows"
			x="item_name"
			:y="sortBy"
			horizontal
			:y-axis="{ format: formatValue }"
			:series-config="{
				revenue: { label: 'Revenue' },
				units: { label: 'Units' },
			}"
			:loading="topProducts.loading && !topProducts.data"
			:error="topProducts.error?.message ?? null"
			@select="openProduct"
		>
			<template #actions>
				<TabButtons v-model="sortBy" :options="sortOptions" />
			</template>
			<template #empty>
				<span class="text-p-sm text-ink-gray-5">
					Nothing sold in this period.
				</span>
			</template>
		</BarChart>
	</ChartCard>
</template>
