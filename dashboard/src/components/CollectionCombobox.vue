<script setup lang="ts">
import { useLinkSearch } from "@/composables/useLinkSearch"
import { Combobox } from "frappe-ui"
import { computed } from "vue"

const props = defineProps<{ required?: boolean }>()

const collection = defineModel<string>({ required: true })

/** Surfaced so the host dialog can stand down from outside-dismissal while this popover owns the click. */
const open = defineModel<boolean>("open", { default: false })

const { query, results } = useLinkSearch<string>(
	"/api/v2/method/ls_shop.api.admin.catalog.get_collections",
	() => ({}),
	() => collection.value,
	open,
)

const options = computed(() => results.data ?? [])

const selected = computed({
	get: () => collection.value || null,
	set: (value: string | null) => {
		collection.value = value ?? ""
	},
})
</script>

<template>
	<Combobox
		v-model="selected"
		v-model:open="open"
		v-model:query="query"
		label="Collection"
		placeholder="Search collections"
		:options="options"
		:filterable="false"
		:loading="results.loading"
		:required="props.required"
	/>
</template>
