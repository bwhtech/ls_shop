<script setup lang="ts">
import ListSkeleton from "@/components/ListSkeleton.vue"
import { ChartCard } from "frappe-ui/charts"

withDefaults(
	defineProps<{
		title: string
		subtitle?: string
		loading?: boolean
		error?: string | null
		empty?: boolean
		emptyMessage?: string
		skeletonRows?: number
	}>(),
	{ emptyMessage: "Nothing to show yet.", skeletonRows: 4 },
)
</script>

<!--
	The card every non-chart widget on the analytics page sits in.

	`ChartCard` draws the surface and `ChartContainer` the header, but the container sizes its
	body to a plot and floats the states over it - which a table of unknown height cannot give
	it. This keeps the container's header and its four states, laid out for content that grows.
-->
<template>
	<ChartCard>
		<div class="flex h-full flex-col gap-3">
			<div class="flex items-start justify-between gap-3">
				<div class="min-w-0">
					<div class="truncate text-p-base text-ink-gray-8">{{ title }}</div>
					<div v-if="subtitle" class="truncate text-p-sm text-ink-gray-5">
						{{ subtitle }}
					</div>
				</div>
				<div v-if="$slots.actions" class="shrink-0">
					<slot name="actions" />
				</div>
			</div>

			<ListSkeleton v-if="loading" :rows="skeletonRows" />

			<div
				v-else-if="error"
				class="flex flex-col items-center gap-1 py-6 text-center"
			>
				<span class="text-sm-medium text-ink-red-7">
					Could not load this widget
				</span>
				<span class="max-w-sm text-p-sm text-ink-gray-5">{{ error }}</span>
			</div>

			<div v-else-if="empty" class="py-6 text-center">
				<slot name="empty">
					<span class="text-p-sm text-ink-gray-5">{{ emptyMessage }}</span>
				</slot>
			</div>

			<div v-else class="min-h-0 flex-1">
				<slot />
			</div>
		</div>
	</ChartCard>
</template>
