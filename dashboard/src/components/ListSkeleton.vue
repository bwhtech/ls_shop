<script setup lang="ts">
import { Skeleton } from "frappe-ui"
import { computed } from "vue"

type SkeletonColumn = { width?: number | string }

const props = withDefaults(
	defineProps<{ columns: SkeletonColumn[]; rows?: number }>(),
	{ rows: 6 },
)

// frappe-ui does not export `getGridTemplateColumns`, so the same fr maths is repeated here.
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

<!-- `ListView` has no loading prop - it renders its empty state whenever `rows` is empty. -->
<template>
	<div class="relative flex w-full flex-1 flex-col overflow-x-auto">
		<!-- A placeholder row has no text, so the grid tracks need a width floor or they collapse to 1px. -->
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
