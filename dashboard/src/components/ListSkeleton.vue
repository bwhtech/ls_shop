<script setup lang="ts">
import { Skeleton } from "frappe-ui"
import { computed } from "vue"

type SkeletonColumn = { width?: number | string }

const props = withDefaults(
	defineProps<{ columns: SkeletonColumn[]; rows?: number }>(),
	{ rows: 6 },
)

// frappe-ui keeps getGridTemplateColumns in ListView/utils.js and does not export it from the
// package, so the same fr maths is repeated here. Without it the placeholder sits on its own grid
// and every row jumps sideways the moment real rows replace it.
const gridTemplateColumns = computed(() =>
	props.columns
		.map((column) =>
			typeof column.width === "number"
				? `${column.width}fr`
				: column.width || "1fr",
		)
		.join(" "),
)
</script>

<!--
	Placeholder rows for a list that is still loading.

	`ListView` has no loading prop - it renders its empty state whenever `rows` is empty - so a list
	left to its own devices announces "No products yet" on every first load. Geometry here mirrors
	ListRow: a 40px row, a 1px divider, `gap-4 px-2`, and the caller's own column widths.
-->
<template>
	<div class="relative flex w-full flex-1 flex-col overflow-x-auto">
		<!-- ListView.vue wraps its rows in exactly this: w-max lets the grid keep readable columns
		     and scroll on a narrow screen instead of squeezing them to nothing. A real row is as wide
		     as its text; a placeholder has none, so the tracks need a floor or they collapse to 1px.
		     45rem is a plain guess at "a list is at least this wide" - revisit if a list ever wants
		     more than about six columns. -->
		<div class="flex w-max min-w-full flex-col">
			<div class="mb-2 h-[31px] min-w-[45rem] rounded-4 bg-surface-gray-2" />

			<div v-for="row in rows" :key="row">
				<div
					class="grid h-10 min-w-[45rem] items-center gap-4 px-2"
					:style="{ gridTemplateColumns }"
				>
					<Skeleton
						v-for="(column, index) in columns"
						:key="index"
						class="h-3.5"
						:class="index === 0 ? 'w-3/4' : 'w-1/2'"
					/>
				</div>
				<div class="h-px bg-surface-gray-2" />
			</div>
		</div>
	</div>
</template>
