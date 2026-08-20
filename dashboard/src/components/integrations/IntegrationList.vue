<script setup lang="ts">
import { Skeleton, dialog, toast } from "frappe-ui"
import { computed, ref } from "vue"
import IntegrationCard from "./IntegrationCard.vue"
import IntegrationDialog from "./IntegrationDialog.vue"
import {
	type Integration,
	type IntegrationValues,
	integrationErrorMessage,
	useIntegrations,
} from "./useIntegrations"

const props = defineProps<{ listUrl: string; saveUrl: string }>()

const { list, integrations, save, saveIntegration } = useIntegrations({
	listUrl: props.listUrl,
	saveUrl: props.saveUrl,
})

const busySlug = ref<string | null>(null)
const activeSlug = ref<string | null>(null)
const showDialog = ref(false)

const active = computed(
	() =>
		integrations.value.find(
			(integration) => integration.slug === activeSlug.value,
		) ?? null,
)

/** The refusal from the last save attempt made from inside the dialog. */
const dialogError = ref<string | null>(null)

function configure(integration: Integration) {
	activeSlug.value = integration.slug
	dialogError.value = null
	showDialog.value = true
}

async function setEnabled(integration: Integration, enabled: boolean) {
	busySlug.value = integration.slug
	const saved = await saveIntegration({
		slug: integration.slug,
		enabled,
		values: {},
	})
	busySlug.value = null
	if (!saved) toast.error(integrationErrorMessage(save.error))
}

function toggle(integration: Integration, enabled: boolean) {
	if (enabled) {
		setEnabled(integration, true)
		return
	}
	dialog.confirm({
		title: `Turn off ${integration.label}?`,
		message: "Customers will stop seeing it until you turn it back on.",
		theme: "red",
		confirmLabel: "Turn off",
		onConfirm: async () => await setEnabled(integration, false),
	})
}

async function saveActive(payload: {
	enabled: boolean
	values: IntegrationValues
}) {
	const integration = active.value
	if (!integration) return
	dialogError.value = null
	const saved = await saveIntegration({
		slug: integration.slug,
		enabled: payload.enabled,
		values: payload.values,
	})
	if (saved) {
		showDialog.value = false
		return
	}
	dialogError.value = integrationErrorMessage(save.error)
}
</script>

<template>
	<div>
		<div v-if="list.loading && !integrations.length" class="space-y-4 py-4">
			<div v-for="row in 3" :key="row" class="flex items-center gap-4">
				<Skeleton class="h-9 w-24 rounded-md" />
				<div class="flex-1 space-y-2">
					<Skeleton class="h-3.5 w-32" />
					<Skeleton class="h-3 w-64" />
				</div>
			</div>
		</div>

		<div
			v-else-if="!integrations.length"
			class="flex flex-col items-center justify-center gap-2 py-12 text-center"
		>
			<div class="rounded-full bg-surface-gray-2 p-3 text-ink-gray-5">
				<span class="lucide-plug size-5" aria-hidden="true" />
			</div>
			<p class="text-base text-ink-gray-7">Nothing to connect yet</p>
			<p class="text-p-sm text-ink-gray-5">
				Providers show up here once their app is installed on this store.
			</p>
		</div>

		<div v-else class="divide-y divide-outline-gray-1">
			<IntegrationCard
				v-for="integration in integrations"
				:key="integration.slug"
				:integration="integration"
				:busy="busySlug === integration.slug"
				@toggle="(enabled: boolean) => toggle(integration, enabled)"
				@configure="configure(integration)"
			/>
		</div>

		<IntegrationDialog
			v-model:open="showDialog"
			:integration="active"
			:saving="save.loading"
			:error="dialogError"
			@save="saveActive"
		/>
	</div>
</template>
