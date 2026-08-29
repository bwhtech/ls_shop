<script setup lang="ts">
import type { OrderState } from "@/types"
import { orderStateBadge } from "@/utils/format"
import { Badge } from "frappe-ui"
import { computed } from "vue"

const props = defineProps<{ state: OrderState }>()

const badge = computed(() => orderStateBadge(props.state))
</script>

<template>
	<Badge :variant="badge.variant" :theme="badge.theme" :label="state.label">
		<template #prefix>
			<!-- Badge sizes its prefix box at 10px, too small to tell one glyph from another. -->
			<span :class="badge.icon" class="size-3 shrink-0" aria-hidden="true" />
		</template>
	</Badge>
</template>
