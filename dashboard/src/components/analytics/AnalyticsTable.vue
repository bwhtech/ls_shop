<script setup lang="ts">
export type AnalyticsTableColumn = {
	/** Doubles as the slot name, so a cell that needs a badge or a link overrides just that one. */
	key: string
	label: string
	numeric?: boolean
}

type AnalyticsTableRow = Record<string, unknown>

withDefaults(
	defineProps<{
		columns: AnalyticsTableColumn[]
		rows: AnalyticsTableRow[]
		rowKey: string
		clickable?: boolean
	}>(),
	{ clickable: false },
)

const emit = defineEmits<{ select: [row: AnalyticsTableRow] }>()

function selectRow(row: AnalyticsTableRow) {
	emit("select", row)
}
</script>

<!--
	The dense numeric table half the analytics widgets are. Every column is a named slot, so a
	widget styles the two cells it cares about and lets the rest print themselves.
-->
<template>
	<div class="-mx-1 overflow-x-auto">
		<table class="w-full min-w-max border-collapse text-base">
			<thead>
				<tr class="border-b border-outline-gray-1">
					<th
						v-for="column in columns"
						:key="column.key"
						class="whitespace-nowrap px-2 py-1.5 text-p-xs font-medium text-ink-gray-5"
						:class="column.numeric ? 'text-right' : 'text-left'"
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
								? 'whitespace-nowrap text-right tabular-nums'
								: 'max-w-[16rem] truncate text-left'
						"
					>
						<slot :name="column.key" :row="row">{{ row[column.key] }}</slot>
					</td>
				</tr>
			</tbody>
		</table>
	</div>
</template>
