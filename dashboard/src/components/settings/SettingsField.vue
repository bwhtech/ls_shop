<script setup lang="ts">
import { TEXTAREA_FIELDTYPES } from "@/utils/docfield"
import { computed } from "vue"
import DocFieldControl from "./DocFieldControl.vue"
import SettingsLinkField from "./SettingsLinkField.vue"
import type { AdvancedField } from "./types"
import { type SettingsValue, normalizeValue } from "./useSettingsForm"

const props = defineProps<{ field: AdvancedField; modelValue: SettingsValue }>()
const emit = defineEmits<{ "update:modelValue": [value: SettingsValue] }>()

const text = computed<string | null>({
	get: () =>
		props.modelValue === null ? null : normalizeValue(props.modelValue),
	set: (next) => emit("update:modelValue", next),
})

/** Only the multi-line control is widened; the rest size themselves in SettingsRow's column. */
const isTextarea = computed(() =>
	TEXTAREA_FIELDTYPES.includes(props.field.fieldtype),
)
</script>

<template>
	<!-- Advanced links search a Lifestyle Settings-scoped endpoint rather than Frappe's global
	     link search, so the Link branch stays here and the rest of the ladder is shared. -->
	<SettingsLinkField
		v-if="props.field.fieldtype === 'Link'"
		v-model="text"
		:doctype="props.field.options ?? ''"
	/>
	<DocFieldControl
		v-else
		:field="props.field"
		:model-value="props.modelValue"
		:class="isTextarea ? 'w-72' : undefined"
		@update:model-value="emit('update:modelValue', $event)"
	/>
</template>
