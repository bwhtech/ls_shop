<script setup lang="ts">
import {
	Button,
	Checkbox,
	Dialog,
	ErrorMessage,
	FormControl,
	Password,
	Switch,
	toast,
} from "frappe-ui"
import { Link } from "frappe-ui/frappe"
import { computed, reactive, ref, watch } from "vue"
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

const TEXTAREA_FIELDTYPES = ["Small Text", "Text", "Long Text", "Code", "JSON"]
const NUMBER_FIELDTYPES = ["Int", "Float", "Currency", "Percent"]

const enabled = ref(false)
const values = reactive<IntegrationValues>({})
/** A stored secret comes back blank; it is only sent once the owner types a new one. */
const touchedSecrets = reactive<Record<string, boolean>>({})

const fields = computed(() =>
	(props.integration?.groups ?? []).flatMap((group) => group.fields),
)

function isSecret(field: IntegrationField) {
	return field.is_secret || field.fieldtype === "Password"
}

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

function selectOptions(field: IntegrationField) {
	return (field.options ?? "")
		.split("\n")
		.map((option) => ({ label: option, value: option }))
}

/** Data fields carry their input hint in `options` (Email / URL / Phone). */
function textInputType(field: IntegrationField) {
	const hint = (field.options ?? "").toLowerCase()
	if (hint === "email") return "email"
	if (hint === "url") return "url"
	if (hint === "phone") return "tel"
	return "text"
}

/** Docfield descriptions are authored as HTML; the form only has room for their text. */
function plainText(value: string | null) {
	if (!value) return undefined
	return value.replace(/<[^>]*>/g, "").trim() || undefined
}

function secretDescription(field: IntegrationField) {
	if (field.is_set) return "Saved — leave blank to keep it"
	return plainText(field.description)
}

function markSecretTouched(field: IntegrationField) {
	touchedSecrets[field.fieldname] = true
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
					class="flex items-center justify-between gap-4 rounded border border-outline-gray-2 px-3 py-2.5"
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
						<Checkbox
							v-if="field.fieldtype === 'Check'"
							v-model="values[field.fieldname] as boolean"
							:label="field.label"
							:description="plainText(field.description)"
						/>
						<Password
							v-else-if="isSecret(field)"
							v-model="values[field.fieldname] as string"
							:label="field.label"
							:required="field.required"
							:description="secretDescription(field)"
							:placeholder="field.is_set ? '••••••••' : ''"
							@update:model-value="markSecretTouched(field)"
						/>
						<FormControl
							v-else-if="field.fieldtype === 'Select'"
							v-model="values[field.fieldname]"
							type="select"
							:label="field.label"
							:required="field.required"
							:description="plainText(field.description)"
							:options="selectOptions(field)"
						/>
						<FormControl
							v-else-if="TEXTAREA_FIELDTYPES.includes(field.fieldtype)"
							v-model="values[field.fieldname]"
							type="textarea"
							:rows="3"
							:label="field.label"
							:required="field.required"
							:description="plainText(field.description)"
						/>
						<FormControl
							v-else-if="NUMBER_FIELDTYPES.includes(field.fieldtype)"
							v-model="values[field.fieldname]"
							type="number"
							:label="field.label"
							:required="field.required"
							:description="plainText(field.description)"
						/>
						<Link
							v-else-if="field.fieldtype === 'Link'"
							v-model="values[field.fieldname] as string"
							:doctype="field.options ?? ''"
							:label="field.label"
							:required="field.required"
							:description="plainText(field.description)"
						/>
						<FormControl
							v-else
							v-model="values[field.fieldname]"
							:type="textInputType(field)"
							:label="field.label"
							:required="field.required"
							:description="plainText(field.description)"
						/>
					</template>
				</div>

				<div v-if="props.integration.webhook_url" class="space-y-1.5">
					<div class="text-base text-ink-gray-7">Webhook URL</div>
					<div
						class="flex items-center gap-2 rounded border border-outline-gray-2 bg-surface-gray-1 py-1.5 pl-3 pr-1.5"
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
