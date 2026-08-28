<script setup lang="ts">
import { refDebounced } from "@vueuse/core"
import { Combobox, useCall } from "frappe-ui"
import { computed, ref } from "vue"

type LinkSearchResult = {
	value: string
	label?: string
	description?: string
}

const props = defineProps<{
	doctype: string
	label?: string
	description?: string
	error?: string
	required?: boolean
	disabled?: boolean
	placeholder?: string
}>()

const linked_document = defineModel<string>({ default: "" })

const open = ref(false)
const query = ref("")

// A Link docfield with no `options` has nothing to search, and Frappe's own guard treats "" as
// falsy - it would run an unscoped search_widget rather than reject the request. Holding the
// search term still keeps the request URL constant, so `refetch` never fires either.
const searchable = computed(() => Boolean(props.doctype))

// In the combobox's input mode the query IS the value display, so it still reads the committed
// link while the popover is open and nothing has been typed yet. Searching for that text would
// filter the list down to the value already chosen, so only a genuinely different query counts.
const searchText = refDebounced(
	computed(() =>
		searchable.value && open.value && query.value !== linked_document.value
			? query.value
			: "",
	),
	300,
)

const results = useCall<LinkSearchResult[], { doctype: string; txt: string }>({
	url: "/api/v2/method/frappe.desk.search.search_link",
	params: () => ({ doctype: props.doctype, txt: searchText.value }),
	immediate: searchable.value,
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
		:error="props.error"
		:required="props.required"
		:disabled="props.disabled"
		:placeholder="placeholderText"
		:options="options"
		:filterable="false"
		:loading="results.loading"
	/>
</template>
