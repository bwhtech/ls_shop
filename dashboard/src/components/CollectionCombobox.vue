<script setup lang="ts">
import { useLinkSearch } from "@/composables/useLinkSearch"
import { Combobox } from "frappe-ui"
import { computed } from "vue"

const props = defineProps<{ required?: boolean }>()

const collection = defineModel<string>({ required: true })

const { open, query, results } = useLinkSearch<string>(
	"/api/v2/method/ls_shop.api.admin.catalog.get_collections",
	() => ({}),
	() => collection.value,
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
