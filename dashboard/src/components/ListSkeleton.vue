<script setup lang="ts">
import { Skeleton } from "frappe-ui"

withDefaults(defineProps<{ rows?: number }>(), { rows: 6 })
</script>

<!--
	Placeholder rows for a list that is still loading.

	`ListView` has no loading prop - it renders its empty state whenever `rows` is empty - so a list
	left to its own devices announces "No products yet" on every first load and every refetch. Each
	list page shows this instead until its first rows land.
-->
<template>
	<div class="space-y-3 py-3">
		<div v-for="row in rows" :key="row" class="flex items-center gap-4">
			<Skeleton class="size-6 shrink-0 rounded-4" />
			<Skeleton class="h-3.5 flex-1" />
			<Skeleton class="h-3.5 w-24 shrink-0" />
			<Skeleton class="h-3.5 w-16 shrink-0" />
		</div>
	</div>
</template>
