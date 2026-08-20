<script setup lang="ts">
import type { OrderState } from "@/types"
import { orderStateBadge } from "@/utils/format"
import { Badge } from "frappe-ui"
import { computed } from "vue"

// Every order badge in the app renders through here, so the list, the detail screen and the Home
// panel cannot drift apart on colour, icon or wording.
const props = defineProps<{ state: OrderState }>()

const badge = computed(() => orderStateBadge(props.state))
</script>

<template>
	<Badge :variant="badge.variant" :theme="badge.theme" :label="state.label">
		<template #prefix>
			<!-- Badge sizes its own prefix box at 10px, which is too small to tell one glyph from
			     another; the icon overrides that to 12px and overflows into the badge's padding. -->
			<span :class="badge.icon" class="size-3 shrink-0" aria-hidden="true" />
		</template>
	</Badge>
</template>
