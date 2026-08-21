<script setup lang="ts">
import type { AnalyticsKpi, AnalyticsKpiKey, AnalyticsOverview } from "@/types"
import { formatCount, formatMoney, formatPercent } from "@/utils/format"
import { NumberCard } from "frappe-ui/charts"
import { computed } from "vue"

const props = defineProps<{
	overview: AnalyticsOverview | null
	currency: string
	loading?: boolean
	error?: string | null
}>()

type TileKind = "money" | "count" | "rate"

const tiles: { key: AnalyticsKpiKey; title: string; kind: TileKind }[] = [
	{ key: "total_sales", title: "Total sales", kind: "money" },
	{ key: "orders", title: "Orders", kind: "count" },
	{ key: "sessions", title: "Sessions", kind: "count" },
	{ key: "conversion_rate", title: "Conversion rate", kind: "rate" },
	{ key: "aov", title: "Avg order value", kind: "money" },
	{
		key: "returning_customer_rate",
		title: "Returning customers",
		kind: "rate",
	},
]

function formatTileValue(value: number, kind: TileKind) {
	if (kind === "money") return formatMoney(value, props.currency, true)
	if (kind === "rate") return formatPercent(value)
	return formatCount(value)
}

/**
 * A rate moves in percentage points, not in percent: conversion 4.7% -> 4.9% is +0.2 pp, and
 * printing the +4.3% relative change instead would read as a move twenty times the size.
 */
function tileDelta(kpi: AnalyticsKpi | undefined, kind: TileKind) {
	if (!kpi) return null
	if (kind === "rate") return Number((kpi.value - kpi.previous).toFixed(1))
	if (!kpi.previous) return null
	return Number((((kpi.value - kpi.previous) / kpi.previous) * 100).toFixed(1))
}

const cards = computed(() =>
	tiles.map((tile) => {
		const kpi = props.overview?.kpis?.[tile.key]
		return {
			title: tile.title,
			value: kpi ? formatTileValue(kpi.value, tile.kind) : null,
			delta: tileDelta(kpi, tile.kind),
			deltaSuffix: tile.kind === "rate" ? " pp" : "%",
		}
	}),
)
</script>

<template>
	<div class="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
		<NumberCard
			v-for="card in cards"
			:key="card.title"
			:title="card.title"
			:value="card.value"
			:delta="card.delta"
			:delta-suffix="card.deltaSuffix"
			delta-caption="vs previous period"
			:loading="loading"
			:error="error"
		/>
	</div>
</template>
