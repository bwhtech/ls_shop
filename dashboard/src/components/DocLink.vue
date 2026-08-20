<script setup lang="ts">
import { refDebounced } from "@vueuse/core"
import { Combobox, useCall } from "frappe-ui"
import { computed, ref, watch } from "vue"

type LinkSearchResult = {
	value: string
	label?: string
	description?: string
}

const props = defineProps<{
	doctype: string
	label?: string
	description?: string
	required?: boolean
	disabled?: boolean
	placeholder?: string
}>()

const linked_document = defineModel<string | null>({ default: null })

const open = ref(false)
const query = ref("")

// The combobox keeps the input showing the committed label while it is closed, so a closed
// picker must not search for its own value - only a query typed into an open popover counts.
watch(open, (isOpen) => {
	if (isOpen) query.value = ""
})

const searchText = refDebounced(
	computed(() => (open.value ? query.value : "")),
	300,
)

const results = useCall<LinkSearchResult[]>({
	url: "/api/v2/method/frappe.desk.search.search_link",
	params: () => ({ doctype: props.doctype, txt: searchText.value }),
	refetch: true,
})

const options = computed(() =>
	(results.data ?? []).map((result) => ({
		label: result.label || result.value,
		value: result.value,
		description: result.description,
	})),
)

const placeholderText = computed(
	() => props.placeholder ?? `Search ${props.doctype.toLowerCase()}`,
)

const selected = computed({
	get: () => linked_document.value || null,
	set: (value: string | null) => {
		linked_document.value = value ?? ""
	},
})
</script>

<template>
	<Combobox
		v-model="selected"
		v-model:open="open"
		v-model:query="query"
		:label="props.label"
		:description="props.description"
		:required="props.required"
		:disabled="props.disabled"
		:placeholder="placeholderText"
		:options="options"
		:filterable="false"
		:loading="results.loading"
	/>
</template>
