<script setup lang="ts">
import { isSecret, plainText } from "@/utils/docfield"
import { Button, Dialog, ErrorMessage, Switch, toast } from "frappe-ui"
import { computed, reactive, ref, watch } from "vue"
import DocLink from "../DocLink.vue"
import DocFieldControl from "../settings/DocFieldControl.vue"
import { normalizeValue } from "../settings/useSettingsForm"
import type {
	Integration,
	IntegrationField,
	IntegrationValues,
} from "./useIntegrations"

const props = defineProps<{
	integration: Integration | null
	saving?: boolean
	error?: string | null
}>()

const emit = defineEmits<{
	save: [payload: { enabled: boolean; values: IntegrationValues }]
}>()

const open = defineModel<boolean>("open", { required: true })

const enabled = ref(false)
const values = reactive<IntegrationValues>({})
/** A stored secret comes back blank; it is only sent once the owner types a new one. */
const touchedSecrets = reactive<Record<string, boolean>>({})

const fields = computed(() =>
	(props.integration?.groups ?? []).flatMap((group) => group.fields),
)

function initialValue(field: IntegrationField) {
	if (isSecret(field)) return ""
	if (field.fieldtype === "Check") return Boolean(field.value)
	return field.value ?? ""
}

function reset() {
	for (const fieldname of Object.keys(values)) delete values[fieldname]
	for (const fieldname of Object.keys(touchedSecrets))
		delete touchedSecrets[fieldname]
	enabled.value = props.integration?.enabled ?? false
	for (const field of fields.value)
		values[field.fieldname] = initialValue(field)
}

watch(() => [props.integration, open.value], reset, { immediate: true })

const changed = computed(() => {
	if (!props.integration) return false
	if (enabled.value !== props.integration.enabled) return true
	return fields.value.some((field) => {
		if (isSecret(field)) return Boolean(touchedSecrets[field.fieldname])
		return (
			normalizeValue(values[field.fieldname]) !== normalizeValue(field.value)
		)
	})
})

function fieldDescription(field: IntegrationField) {
	if (isSecret(field) && field.is_set) return "Saved — leave blank to keep it"
	return plainText(field.description)
}

function secretPlaceholder(field: IntegrationField) {
	return isSecret(field) && field.is_set ? "••••••••" : undefined
}

function markTouched(field: IntegrationField) {
	if (isSecret(field)) touchedSecrets[field.fieldname] = true
}

function payloadValues(): IntegrationValues {
	const payload: IntegrationValues = {}
	for (const field of fields.value) {
		if (isSecret(field) && !touchedSecrets[field.fieldname]) continue
		payload[field.fieldname] = values[field.fieldname] ?? null
	}
	return payload
}

function submit() {
	emit("save", { enabled: enabled.value, values: payloadValues() })
}

async function copyWebhookUrl() {
	const url = props.integration?.webhook_url
	if (!url) return
	await navigator.clipboard.writeText(url)
	toast.success("Webhook URL copied")
}
</script>

<template>
	<Dialog v-model:open="open" :title="props.integration?.label ?? ''" size="2xl">
		<template #default>
			<div v-if="props.integration" class="space-y-6">
				<p class="text-p-base text-ink-gray-6">{{ props.integration.blurb }}</p>

				<div
					class="flex items-center justify-between gap-4 rounded-4 border border-outline-gray-2 px-3 py-2.5"
				>
					<div class="min-w-0">
						<div class="text-base text-ink-gray-8">Enable this integration</div>
						<p class="mt-0.5 text-p-sm text-ink-gray-5">
							Customers only see it at checkout while it is on.
						</p>
					</div>
					<Switch v-model="enabled" />
				</div>

				<div
					v-for="group in props.integration.groups"
					:key="group.label"
					class="space-y-4"
				>
					<h4 class="text-sm text-ink-gray-5">{{ group.label }}</h4>

					<template v-for="field in group.fields" :key="field.fieldname">
						<!-- Integration links search any doctype through Frappe's own link search;
						     the settings tabs search a scoped endpoint, so each keeps its Link branch. -->
						<DocLink
							v-if="field.fieldtype === 'Link'"
							v-model="values[field.fieldname] as string"
							:doctype="field.options ?? ''"
							:label="field.label"
							:required="field.required"
							:description="fieldDescription(field)"
						/>
						<DocFieldControl
							v-else
							v-model="values[field.fieldname]"
							:field="field"
							:label="field.label"
							:description="fieldDescription(field)"
							:placeholder="secretPlaceholder(field)"
							@update:model-value="markTouched(field)"
						/>
					</template>
				</div>

				<div v-if="props.integration.webhook_url" class="space-y-1.5">
					<div class="text-base text-ink-gray-7">Webhook URL</div>
					<div
						class="flex items-center gap-2 rounded-4 border border-outline-gray-2 bg-surface-gray-1 py-1.5 pl-3 pr-1.5"
					>
						<span class="min-w-0 flex-1 truncate text-p-sm text-ink-gray-7">
							{{ props.integration.webhook_url }}
						</span>
						<Button
							icon="lucide-copy"
							aria-label="Copy webhook URL"
							@click="copyWebhookUrl"
						/>
					</div>
					<p class="text-p-sm text-ink-gray-5">
						Paste this into the provider's dashboard so it can notify your store.
					</p>
				</div>

				<Button
					v-if="props.integration.docs_url"
					:link="props.integration.docs_url"
					variant="ghost"
					label="Open the provider's setup page"
					icon-right="lucide-external-link"
				/>
			</div>
		</template>

		<template #actions="{ close }">
			<div class="space-y-2">
				<ErrorMessage :message="props.error ?? undefined" />
				<div class="flex justify-end gap-2">
					<Button label="Cancel" @click="close" />
					<Button
						variant="solid"
						theme="gray"
						label="Save"
						:loading="props.saving"
						:disabled="!changed"
						@click="submit"
					/>
				</div>
			</div>
		</template>
	</Dialog>
</template>
