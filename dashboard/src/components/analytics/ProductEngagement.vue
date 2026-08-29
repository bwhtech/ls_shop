<script setup lang="ts">
import {
	useAnalyticsRange,
	useAnalyticsReport,
} from "@/composables/useAnalyticsRange"
import type { ProductEngagementRow } from "@/types"
import { Badge } from "frappe-ui"
import { computed } from "vue"
import AnalyticsPanel from "./AnalyticsPanel.vue"
import AnalyticsTable from "./AnalyticsTable.vue"
import {
	type AnalyticsTableColumn,
	countColumn,
	percentColumn,
} from "./columns"

const emit = defineEmits<{ select: [itemCode: string] }>()

const { rangeParams, rangeCaption } = useAnalyticsRange()

const columns: AnalyticsTableColumn<ProductEngagementRow>[] = [
	{ key: "item_name", label: "Product" },
	countColumn("views", "Views"),
	countColumn("adds", "Adds"),
	countColumn("purchases", "Purchases"),
	percentColumn("purchase_to_view_rate", "View → purchase"),
]

const { data, loading, error } = useAnalyticsReport<ProductEngagementRow[]>(
	"get_product_engagement",
	() => ({ ...rangeParams.value, limit: 8 }),
)

const rows = computed(() => data.value ?? [])

function isLowConverting(row: ProductEngagementRow) {
	return row.views > 50 && row.purchase_to_view_rate < 1
}
</script>

<template>
	<AnalyticsPanel
		title="Product engagement"
		:subtitle="`Views to purchases, product by product · ${rangeCaption}`"
		:loading="loading"
		:error="error"
		:empty="!rows.length"
		empty-message="No product views were tracked in this period."
	>
		<AnalyticsTable
			:columns="columns"
			:rows="rows"
			row-key="item_code"
			clickable
			@select="(row) => emit('select', row.item_code)"
		>
			<template #item_name="{ row }">
				<span class="flex items-center gap-2">
					<span class="truncate">{{ row.item_name }}</span>
					<Badge
						v-if="isLowConverting(row)"
						theme="amber"
						variant="subtle"
						label="Low conv"
					/>
				</span>
			</template>
		</AnalyticsTable>
	</AnalyticsPanel>
</template>
