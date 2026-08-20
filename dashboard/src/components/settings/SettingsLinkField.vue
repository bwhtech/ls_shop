<script setup lang="ts">
import { FormControl, useCall } from "frappe-ui"
import { computed } from "vue"

type LinkOption = { label: string; value: string }

const props = defineProps<{
	modelValue: string | null
	/** Doctype the link points at; must be linked from Lifestyle Settings. */
	doctype: string
	disabled?: boolean
}>()

const emit = defineEmits<{ "update:modelValue": [value: string | null] }>()

const links = useCall<LinkOption[]>({
	url: "/api/v2/method/ls_shop.api.admin.settings.get_link_options",
	params: { doctype: props.doctype },
})

// A blank entry so an optional link can be cleared without leaving the dropdown.
const options = computed(() => [
	{ label: "", value: "" },
	...(links.data ?? []),
])

const selected = computed({
	get: () => props.modelValue ?? "",
	set: (value: string) => emit("update:modelValue", value || null),
})
</script>

<template>
	<FormControl
		v-model="selected"
		type="select"
		:options="options"
		:disabled="props.disabled || links.loading"
	/>
</template>
