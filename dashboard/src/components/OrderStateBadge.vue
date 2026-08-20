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
	<Badge variant="subtle" :theme="badge.theme" :label="state.label">
		<template #prefix>
			<span :class="badge.icon" class="size-full" aria-hidden="true" />
		</template>
	</Badge>
</template>
