<script setup lang="ts">
import {
	onAnalyticsRefresh,
	useAnalyticsRange,
} from "@/composables/useAnalyticsRange"
import type {
	AbandonedCartStatus,
	AbandonedCarts,
	AnalyticsRangeParams,
	BadgeTheme,
} from "@/types"
import {
	formatCount,
	formatDateTime,
	formatMoney,
	formatPercent,
} from "@/utils/format"
import { Badge, useCall } from "frappe-ui"
import { computed } from "vue"
import AnalyticsPanel from "./AnalyticsPanel.vue"
import AnalyticsTable from "./AnalyticsTable.vue"
import type { AnalyticsTableColumn } from "./AnalyticsTable.vue"
import StatChip from "./StatChip.vue"

const props = defineProps<{ currency: string }>()

const { rangeParams, rangeCaption } = useAnalyticsRange()

const columns: AnalyticsTableColumn[] = [
	{ key: "customer", label: "Customer" },
	{ key: "items_count", label: "Items", numeric: true },
	{ key: "value", label: "Value", numeric: true },
	{ key: "last_activity", label: "Last activity" },
	{ key: "status", label: "Status" },
	{ key: "quotation", label: "" },
]

/** Recovered is the win, recoverable is the one worth an email, abandoned is just gone. */
const statusThemes: Record<AbandonedCartStatus, BadgeTheme> = {
	Abandoned: "gray",
	Recoverable: "amber",
	Recovered: "green",
}

const abandonedCarts = useCall<AbandonedCarts, AnalyticsRangeParams>({
	url: "/api/v2/method/ls_shop.api.analytics_dashboard.get_abandoned_carts",
	params: () => rangeParams.value,
	refetch: true,
})

onAnalyticsRefresh(() => abandonedCarts.reload())

const stats = computed(() => abandonedCarts.data?.stats)
const carts = computed(() => abandonedCarts.data?.carts ?? [])

const chips = computed(() => {
	if (!stats.value) return []
	return [
		{ label: "Abandoned carts", value: formatCount(stats.value.count) },
		{
			label: "Abandoned value",
			value: formatMoney(stats.value.value, props.currency),
		},
		{ label: "Abandonment rate", value: formatPercent(stats.value.rate) },
	]
})
</script>

<template>
	<AnalyticsPanel
		title="Abandoned carts"
		:subtitle="`Carts left behind — and what they are worth · ${rangeCaption}`"
		:loading="abandonedCarts.loading && !abandonedCarts.data"
		:error="abandonedCarts.error?.message ?? null"
		:empty="!chips.length"
		empty-message="No carts were started in this period."
	>
		<div class="space-y-3">
			<div class="grid grid-cols-1 gap-2 sm:grid-cols-3">
				<StatChip
					v-for="chip in chips"
					:key="chip.label"
					:label="chip.label"
					:value="chip.value"
				/>
			</div>

			<AnalyticsTable
				v-if="carts.length"
				:columns="columns"
				:rows="carts"
				row-key="session_id"
			>
				<template #customer="{ row }">
					{{ row.customer || row.email || "Guest" }}
				</template>
				<template #items_count="{ row }">
					{{ formatCount(Number(row.items_count)) }}
				</template>
				<template #value="{ row }">
					{{ formatMoney(Number(row.value), props.currency) }}
				</template>
				<template #last_activity="{ row }">
					{{ formatDateTime(String(row.last_activity)) }}
				</template>
				<template #status="{ row }">
					<Badge
						:theme="statusThemes[row.status as AbandonedCartStatus]"
						variant="subtle"
						:label="String(row.status)"
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
