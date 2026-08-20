<script setup lang="ts">
import { Checkbox, FormControl } from "frappe-ui"
import { computed } from "vue"
import SettingsAttach from "./SettingsAttach.vue"
import SettingsLinkField from "./SettingsLinkField.vue"
import type { AdvancedField } from "./types"
import type { SettingsValue } from "./useSettingsForm"

const props = defineProps<{ field: AdvancedField; modelValue: SettingsValue }>()
const emit = defineEmits<{ "update:modelValue": [value: SettingsValue] }>()

const TEXTAREA_FIELDTYPES = [
	"Small Text",
	"Text",
	"Long Text",
	"Text Editor",
	"Code",
	"JSON",
]
const NUMBER_FIELDTYPES = ["Int", "Float", "Currency", "Percent"]

const value = computed({
	get: () => props.modelValue,
	set: (next: SettingsValue) => emit("update:modelValue", next),
})

/** Data fields carry their input hint in `options` (Email / URL / Phone). */
const textInputType = computed(() => {
	const hint = (props.field.options ?? "").toLowerCase()
	if (hint === "email") return "email"
	if (hint === "url") return "url"
	if (hint === "phone") return "tel"
	return "text"
})

const selectOptions = computed(() =>
	(props.field.options ?? "")
		.split("\n")
		.map((option) => ({ label: option, value: option })),
)
</script>

<template>
	<SettingsLinkField
		v-if="props.field.fieldtype === 'Link'"
		v-model="value"
		:doctype="props.field.options ?? ''"
	/>
	<SettingsAttach
		v-else-if="props.field.fieldtype === 'Attach Image'"
		v-model="value"
	/>
	<SettingsAttach
		v-else-if="props.field.fieldtype === 'Attach'"
		v-model="value"
		:image="false"
	/>
	<Checkbox v-else-if="props.field.fieldtype === 'Check'" v-model="value" />
	<FormControl
		v-else-if="props.field.fieldtype === 'Color'"
		v-model="value"
		type="color"
		class="w-24"
	/>
	<FormControl
		v-else-if="props.field.fieldtype === 'Select'"
		v-model="value"
		type="select"
		:options="selectOptions"
	/>
	<FormControl
		v-else-if="TEXTAREA_FIELDTYPES.includes(props.field.fieldtype)"
		v-model="value"
		type="textarea"
		:rows="props.field.fieldtype === 'Code' ? 8 : 3"
		class="w-72"
	/>
	<FormControl
		v-else-if="NUMBER_FIELDTYPES.includes(props.field.fieldtype)"
		v-model="value"
		type="number"
	/>
	<FormControl v-else v-model="value" :type="textInputType" />
</template>
