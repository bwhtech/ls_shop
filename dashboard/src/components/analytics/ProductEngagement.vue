<script setup lang="ts">
import {
	onAnalyticsRefresh,
	useAnalyticsRange,
} from "@/composables/useAnalyticsRange"
import type { ProductEngagementRow } from "@/types"
import { formatCount, formatPercent } from "@/utils/format"
import { Badge, useCall } from "frappe-ui"
import { computed } from "vue"
import AnalyticsPanel from "./AnalyticsPanel.vue"
import AnalyticsTable from "./AnalyticsTable.vue"
import type { AnalyticsTableColumn } from "./AnalyticsTable.vue"

const emit = defineEmits<{ select: [itemCode: string] }>()

const { rangeParams, rangeCaption } = useAnalyticsRange()

const columns: AnalyticsTableColumn[] = [
	{ key: "item_name", label: "Product" },
	{ key: "views", label: "Views", numeric: true },
	{ key: "adds", label: "Adds", numeric: true },
	{ key: "purchases", label: "Purchases", numeric: true },
	{ key: "purchase_to_view_rate", label: "View → purchase", numeric: true },
]

const engagement = useCall<ProductEngagementRow[]>({
	url: "/api/v2/method/ls_shop.api.analytics_dashboard.get_product_engagement",
	params: () => ({ ...rangeParams.value, limit: 8 }),
	refetch: true,
})

onAnalyticsRefresh(() => engagement.reload())

const rows = computed(() => engagement.data ?? [])

/** The store's own flag from the formula sheet: plenty of interest, almost nothing bought. */
function isLowConverting(row: ProductEngagementRow) {
	return row.views > 50 && row.purchase_to_view_rate < 1
}
</script>

<template>
	<AnalyticsPanel
		title="Product engagement"
		:subtitle="`Views to purchases, product by product · ${rangeCaption}`"
		:loading="engagement.loading && !engagement.data"
		:error="engagement.error?.message ?? null"
		:empty="!rows.length"
		empty-message="No product views were tracked in this period."
	>
		<AnalyticsTable
			:columns="columns"
			:rows="rows"
			row-key="item_code"
			clickable
			@select="(row) => emit('select', String(row.item_code))"
		>
			<template #item_name="{ row }">
				<span class="flex items-center gap-2">
					<span class="truncate">{{ row.item_name }}</span>
					<Badge
						v-if="isLowConverting(row as ProductEngagementRow)"
						theme="amber"
						variant="subtle"
						label="Low conv"
					/>
				</span>
			</template>
			<template #views="{ row }">{{ formatCount(Number(row.views)) }}</template>
			<template #adds="{ row }">{{ formatCount(Number(row.adds)) }}</template>
			<template #purchases="{ row }">
				{{ formatCount(Number(row.purchases)) }}
			</template>
			<template #purchase_to_view_rate="{ row }">
				{{ formatPercent(Number(row.purchase_to_view_rate)) }}
			</template>
		</AnalyticsTable>
	</AnalyticsPanel>
</template>
