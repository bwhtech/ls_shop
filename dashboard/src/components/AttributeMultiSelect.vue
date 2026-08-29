<script setup lang="ts">
import { errorMessage } from "@/utils/errors"
import { Button, MultiSelect, toast, useCall } from "frappe-ui"
import { computed, ref } from "vue"

const props = defineProps<{
	attribute: string
	label: string
	placeholder?: string
	description?: string
}>()

const selected = defineModel<string[]>({ required: true })

const values = useCall<string[], { attribute: string }>({
	url: "/api/v2/method/ls_shop.api.admin.catalog.get_attribute_values",
	params: () => ({ attribute: props.attribute }),
	onError: (error: { message?: string }) =>
		toast.error(
			errorMessage(error, `Could not load ${props.label.toLowerCase()}`),
		),
})

/** A value the owner types lives only in this picker until the product is created, so it is held here. */
const added = ref<string[]>([])

const options = computed(() =>
	[...(values.data ?? []), ...added.value].map((value) => ({
		label: value,
		value,
	})),
)

/** ERPNext matches attribute values case-insensitively, so "red" beside "Red" would add nothing new. */
function canAdd(query: string) {
	const typed = query.trim()
	return (
		Boolean(typed) &&
		!options.value.some(
			(option) => option.value.toLowerCase() === typed.toLowerCase(),
		)
	)
}

function add(query: string, setQuery: (value: string) => void) {
	const typed = query.trim()
	added.value.push(typed)
	selected.value = [...selected.value, typed]
	setQuery("")
}
</script>

<template>
	<MultiSelect
		v-model="selected"
		:label="props.label"
		:placeholder="props.placeholder"
		:description="props.description"
		:options="options"
		:loading="values.loading"
	>
		<template #summary="{ summary, selectedOptions }">
			{{
				selectedOptions.length
					? selectedOptions.map((option) => option.label).join(", ")
					: summary
			}}
		</template>
		<template #search-suffix="{ query, setQuery }">
			<Button
				v-if="canAdd(query)"
				variant="ghost"
				icon="lucide-plus"
				:aria-label="`Add ${query.trim()}`"
				@click="add(query, setQuery)"
			/>
		</template>
	</MultiSelect>
</template>
