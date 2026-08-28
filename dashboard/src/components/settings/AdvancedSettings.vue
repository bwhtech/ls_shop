<script setup lang="ts">
import { errorMessage } from "@/utils/errors"
import {
	Alert,
	SettingsBody,
	SettingsHeader,
	SettingsRow,
	toast,
	useCall,
} from "frappe-ui"
import { computed, reactive, watch } from "vue"
import SettingsField from "./SettingsField.vue"
import SettingsSaveButton from "./SettingsSaveButton.vue"
import type { AdvancedField } from "./types"
import { type SettingsValue, normalizeValue } from "./useSettingsForm"

type AdvancedGroup = {
	label: string
	fields: (AdvancedField & { value: SettingsValue })[]
}
type ChildTable = { label: string; options: string }
type AdvancedSettings = { groups: AdvancedGroup[]; child_tables: ChildTable[] }

const advanced = useCall<AdvancedSettings>({
	url: "/api/v2/method/ls_shop.api.admin.settings.get_advanced_settings",
})

const form = reactive<Record<string, SettingsValue>>({})
const loaded = reactive<Record<string, SettingsValue>>({})

watch(
	() => advanced.data,
	(data) => {
		if (!data) return
		for (const group of data.groups) {
			for (const field of group.fields) {
				form[field.fieldname] = field.value ?? null
				loaded[field.fieldname] = field.value ?? null
			}
		}
	},
	{ immediate: true },
)

// Only the fields the owner actually touched go back, so a save never rewrites the rest of
// the doctype with values it merely rendered.
const changedValues = computed(() => {
	const changes: Record<string, SettingsValue> = {}
	for (const fieldname of Object.keys(form)) {
		if (normalizeValue(form[fieldname]) !== normalizeValue(loaded[fieldname])) {
			changes[fieldname] = form[fieldname]
		}
	}
	return changes
})

const changed = computed(() => Object.keys(changedValues.value).length > 0)

const save = useCall<unknown, Record<string, SettingsValue>>({
	url: "/api/v2/method/ls_shop.api.admin.settings.save_advanced_settings",
	method: "POST",
	immediate: false,
	onSuccess: () => {
		toast.success("Advanced settings saved")
		advanced.reload()
	},
	onError: (error: Error) => toast.error(errorMessage(error)),
})
</script>

<template>
	<SettingsHeader
		title="Advanced"
		description="Every remaining Lifestyle Settings field, grouped as it appears in Desk"
	/>

	<SettingsBody>
		<div class="space-y-8 pt-6">
			<Alert
				theme="amber"
				title="These are setup values, not everyday settings"
				description="Changing them can break your storefront — edit only what you recognise."
			/>

			<section v-for="group in advanced.data?.groups ?? []" :key="group.label">
				<h3 class="text-base font-medium text-ink-gray-8">{{ group.label }}</h3>
				<div class="mt-1 divide-y divide-outline-gray-1">
					<SettingsRow
						v-for="field in group.fields"
						:key="field.fieldname"
						:title="field.label"
						:description="field.description ?? undefined"
					>
						<SettingsField :field="field" v-model="form[field.fieldname]" />
					</SettingsRow>
				</div>
			</section>

			<section v-if="advanced.data?.child_tables?.length">
				<h3 class="text-base font-medium text-ink-gray-8">Managed in Desk</h3>
				<p class="mt-1 text-p-sm text-ink-gray-5">
					These are lists of rows rather than single values, so they are still edited in Desk.
				</p>
				<ul class="mt-3 divide-y divide-outline-gray-1 border-y border-outline-gray-1">
					<li
						v-for="table in advanced.data.child_tables"
						:key="table.label"
						class="flex items-center justify-between gap-4 py-2.5"
					>
						<span class="text-base text-ink-gray-8">{{ table.label }}</span>
						<span class="text-sm text-ink-gray-5">{{ table.options }}</span>
					</li>
				</ul>
			</section>

			<SettingsSaveButton
				:loading="save.loading"
				:disabled="!changed"
				@save="save.submit({ ...changedValues })"
			/>
		</div>
	</SettingsBody>
</template>
