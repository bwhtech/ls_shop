<script setup lang="ts" generic="TRow extends Record<string, unknown>">
import ScrollFade from "@/components/ScrollFade.vue"
import type { AnalyticsTableColumn } from "./columns"

withDefaults(
	defineProps<{
		columns: AnalyticsTableColumn<TRow>[]
		rows: TRow[]
		rowKey: string
		clickable?: boolean
	}>(),
	{ clickable: false },
)

const emit = defineEmits<{ select: [row: TRow] }>()

function selectRow(row: TRow) {
	emit("select", row)
}
</script>

<template>
	<ScrollFade orientation="horizontal" class="-mx-1">
		<table class="w-full min-w-max border-collapse text-base">
			<thead>
				<tr class="border-b border-outline-gray-1">
					<th
						v-for="column in columns"
						:key="column.key"
						class="whitespace-nowrap px-2 py-1.5 text-p-xs font-medium text-ink-gray-5"
						:class="column.numeric ? 'text-end' : 'text-start'"
					>
						{{ column.label }}
					</th>
				</tr>
			</thead>
			<tbody>
				<tr
					v-for="row in rows"
					:key="String(row[rowKey])"
					class="border-b border-outline-gray-1 last:border-0"
					:class="
						clickable
							? 'cursor-pointer outline-none hover:bg-surface-gray-2 focus-visible:bg-surface-gray-2'
							: undefined
					"
					:tabindex="clickable ? 0 : undefined"
					@click="clickable && selectRow(row)"
					@keydown.enter="clickable && selectRow(row)"
				>
					<td
						v-for="column in columns"
						:key="column.key"
						class="px-2 py-2 text-ink-gray-8"
						:class="
							column.numeric
								? 'whitespace-nowrap text-end tabular-nums'
								: 'max-w-[16rem] truncate text-start'
						"
					>
						<slot :name="column.key" :row="row">
							{{ column.format ? column.format(row[column.key], row) : row[column.key] }}
						</slot>
					</td>
				</tr>
			</tbody>
		</table>
	</ScrollFade>
</template>
