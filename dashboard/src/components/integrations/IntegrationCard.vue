<script setup lang="ts">
import type { BadgeTheme } from "@/types"
import { Badge, Button, Switch, Tooltip } from "frappe-ui"
import { computed } from "vue"
import IntegrationLogo from "./IntegrationLogo.vue"
import type { Integration } from "./useIntegrations"

const props = defineProps<{ integration: Integration; busy?: boolean }>()

const emit = defineEmits<{
	toggle: [enabled: boolean]
	configure: []
}>()

type Status = {
	label: string
	theme: BadgeTheme
}

const status = computed<Status>(() => {
	const integration = props.integration
	if (!integration.available) return { label: "Unavailable", theme: "gray" }
	if (integration.enabled) return { label: "Live", theme: "green" }
	if (!integration.configured)
		return { label: "Not configured", theme: "amber" }
	return { label: "Off", theme: "gray" }
})

const unavailableReason = computed(
	() =>
		`Not available on this store — ${props.integration.settings_doctype} is not installed.`,
)
</script>

<template>
	<div class="flex items-center gap-3 py-3">
		<IntegrationLogo :slug="props.integration.slug" :label="props.integration.label" />

		<div class="min-w-0 flex-1">
			<div class="truncate text-base font-medium text-ink-gray-8">
				{{ props.integration.label }}
			</div>
			<p class="mt-0.5 text-p-sm text-ink-gray-5">
				{{ props.integration.available ? props.integration.blurb : unavailableReason }}
			</p>
		</div>

		<div class="w-28 shrink-0">
			<Badge :label="status.label" :theme="status.theme" variant="subtle" />
		</div>

		<Tooltip :text="props.integration.available ? '' : unavailableReason">
			<Switch
				:model-value="props.integration.enabled"
				:disabled="!props.integration.available || props.busy"
				@update:model-value="(enabled: boolean) => emit('toggle', enabled)"
			/>
		</Tooltip>

		<Button
			class="shrink-0"
			label="Configure"
			:disabled="!props.integration.available"
			@click="emit('configure')"
		/>
	</div>
</template>
