<script setup lang="ts">
import {
	type DocField,
	type DocFieldValue,
	NUMBER_FIELDTYPES,
	TEXTAREA_FIELDTYPES,
	isSecret,
	selectOptions,
	textInputType,
} from "@/utils/docfield"
import { Checkbox, FormControl, Password } from "frappe-ui"
import { computed } from "vue"
import SettingsAttach from "./SettingsAttach.vue"
import { normalizeValue } from "./useSettingsForm"

const props = defineProps<{
	field: DocField
	modelValue: DocFieldValue
	/**
	 * The integration forms label each control themselves; the settings tabs put the label in
	 * their SettingsRow, and FormControl renders identically with it left undefined.
	 */
	label?: string
	description?: string
	placeholder?: string
}>()

const emit = defineEmits<{ "update:modelValue": [value: DocFieldValue] }>()

const value = computed({
	get: () => props.modelValue,
	set: (next: DocFieldValue) => emit("update:modelValue", next),
})

// Attach, Password and Checkbox each take one shape, while a metadata-driven field holds any of
// them - so each control reads the value as what it accepts and writes the plain value back.
const text = computed<string | null>({
	get: () =>
		props.modelValue === null ? null : normalizeValue(props.modelValue),
	set: (next) => emit("update:modelValue", next),
})

const checked = computed({
	get: () => normalizeValue(props.modelValue) === "1",
	set: (next: boolean) => emit("update:modelValue", next),
})

/** Password's model is a plain string; a stored-but-hidden secret arrives as an empty one. */
const secret = computed({
	get: () => normalizeValue(props.modelValue),
	set: (next: string) => emit("update:modelValue", next),
})
</script>

<!--
	One ladder from fieldtype to control, so a fieldtype cannot render as a textarea on one
	screen and a one-line input on another. Link is deliberately not here: the settings tabs
	search a permission-scoped endpoint and the integration forms search Frappe's own, so each
	caller keeps its own Link branch above this one.
-->
<template>
	<SettingsAttach
		v-if="props.field.fieldtype === 'Attach Image'"
		v-model="text"
	/>
	<SettingsAttach
		v-else-if="props.field.fieldtype === 'Attach'"
		v-model="text"
		:image="false"
	/>
	<Checkbox
		v-else-if="props.field.fieldtype === 'Check'"
		v-model="checked"
		:label="props.label"
		:description="props.description"
	/>
	<Password
		v-else-if="isSecret(props.field)"
		v-model="secret"
		:label="props.label"
		:description="props.description"
		:placeholder="props.placeholder"
		:required="props.field.required"
	/>
	<FormControl
		v-else-if="props.field.fieldtype === 'Select'"
		v-model="value"
		type="select"
		:options="selectOptions(props.field)"
		:label="props.label"
		:description="props.description"
		:required="props.field.required"
	/>
	<FormControl
		v-else-if="TEXTAREA_FIELDTYPES.includes(props.field.fieldtype)"
		v-model="value"
		type="textarea"
		:rows="props.field.fieldtype === 'Code' ? 8 : 3"
		:label="props.label"
		:description="props.description"
		:placeholder="props.placeholder"
		:required="props.field.required"
	/>
	<FormControl
		v-else-if="NUMBER_FIELDTYPES.includes(props.field.fieldtype)"
		v-model="value"
		type="number"
		:label="props.label"
		:description="props.description"
		:placeholder="props.placeholder"
		:required="props.field.required"
	/>
	<FormControl
		v-else
		v-model="value"
		:type="textInputType(props.field)"
		:label="props.label"
		:description="props.description"
		:placeholder="props.placeholder"
		:required="props.field.required"
	/>
</template>
