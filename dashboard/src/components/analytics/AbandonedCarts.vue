<script setup lang="ts">
import {
	useAnalyticsRange,
	useAnalyticsReport,
} from "@/composables/useAnalyticsRange"
import type {
	AbandonedCartRow,
	AbandonedCartStatus,
	AbandonedCarts,
	BadgeTheme,
} from "@/types"
import {
	formatCount,
	formatDateTime,
	formatMoney,
	formatPercent,
} from "@/utils/format"
import { Badge } from "frappe-ui"
import { NumberCard } from "frappe-ui/charts"
import { computed } from "vue"
import AnalyticsPanel from "./AnalyticsPanel.vue"
import AnalyticsTable from "./AnalyticsTable.vue"
import { type AnalyticsTableColumn, countColumn, moneyColumn } from "./columns"

const props = defineProps<{ currency: string }>()

const { rangeCaption } = useAnalyticsRange()

const columns: AnalyticsTableColumn<AbandonedCartRow>[] = [
	{
		key: "customer",
		label: "Customer",
		format: (_, row) => row.customer || row.email || "Guest",
	},
	countColumn("items_count", "Items"),
	moneyColumn("value", "Value", () => props.currency),
	{
		key: "last_activity",
		label: "Last activity",
		format: (value) => formatDateTime(String(value)),
	},
	{ key: "status", label: "Status" },
	{ key: "quotation", label: "" },
]

/** Recovered is the win, recoverable is the one worth an email, abandoned is just gone. */
const statusThemes: Record<AbandonedCartStatus, BadgeTheme> = {
	Abandoned: "gray",
	Recoverable: "amber",
	Recovered: "green",
}

const { data, loading, error } = useAnalyticsReport<AbandonedCarts>(
	"get_abandoned_carts",
)

const carts = computed(() => data.value?.carts ?? [])

const tiles = computed(() => {
	const stats = data.value?.stats
	if (!stats) return []
	return [
		{ title: "Abandoned carts", value: formatCount(stats.count) },
		{
			title: "Abandoned value",
			value: formatMoney(stats.value, props.currency),
		},
		{ title: "Abandonment rate", value: formatPercent(stats.rate) },
	]
})
</script>

<template>
	<AnalyticsPanel
		title="Abandoned carts"
		:subtitle="`Carts left behind — and what they are worth · ${rangeCaption}`"
		:loading="loading"
		:error="error"
		:empty="!tiles.length"
		empty-message="No carts were started in this period."
	>
		<div class="space-y-3">
			<!-- card=false: the panel already draws the surface these readings sit on. -->
			<div class="grid grid-cols-1 gap-2 sm:grid-cols-3">
				<NumberCard
					v-for="tile in tiles"
					:key="tile.title"
					:title="tile.title"
					:value="tile.value"
					:card="false"
				/>
			</div>

			<AnalyticsTable
				v-if="carts.length"
				:columns="columns"
				:rows="carts"
				row-key="session_id"
			>
				<template #status="{ row }">
					<Badge
						:theme="statusThemes[row.status]"
						variant="subtle"
						:label="row.status"
					/>
				</template>
				<template #quotation="{ row }">
					<a
						v-if="row.quotation"
						class="text-ink-blue-link hover:underline"
						:href="`/app/quotation/${row.quotation}`"
						target="_blank"
						rel="noopener"
					>
						Open
					</a>
				</template>
			</AnalyticsTable>
			<p v-else class="py-4 text-p-sm text-ink-gray-5">
				No abandoned carts in this period. Nice work!
			</p>
		</div>
	</AnalyticsPanel>
</template>
