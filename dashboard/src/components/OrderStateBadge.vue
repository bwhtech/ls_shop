<script setup lang="ts">
import type { OrderState } from "@/types"
import { orderStateIcon, orderStateTheme } from "@/utils/format"
import { Badge } from "frappe-ui"

// Every order badge in the app renders through here, so the list, the detail screen and the Home
// panel cannot drift apart on colour, icon or wording.
defineProps<{ state: OrderState }>()
</script>

<template>
	<Badge variant="subtle" :theme="orderStateTheme(state)" :label="state.label">
		<template #prefix>
			<span :class="orderStateIcon(state)" class="size-full" aria-hidden="true" />
		</template>
	</Badge>
</template>
