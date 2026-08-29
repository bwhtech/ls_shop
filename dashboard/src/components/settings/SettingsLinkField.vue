<script setup lang="ts">
import { useLinkSearch } from "@/composables/useLinkSearch"
import { Combobox } from "frappe-ui"
import { computed } from "vue"

type LinkOption = { label: string; value: string }

const props = defineProps<{
	modelValue: string | null
	doctype: string
	disabled?: boolean
}>()

const emit = defineEmits<{ "update:modelValue": [value: string | null] }>()

const { open, query, results } = useLinkSearch<LinkOption>(
	"/api/v2/method/ls_shop.api.admin.settings.get_link_options",
	() => ({ doctype: props.doctype }),
	() => props.modelValue,
)

const options = computed(() => results.data ?? [])

const selected = computed({
	get: () => props.modelValue,
	set: (value: string | null) => emit("update:modelValue", value || null),
})
</script>

<template>
	<Combobox
		v-model="selected"
		v-model:open="open"
		v-model:query="query"
		class="w-72"
		:options="options"
		:filterable="false"
		:loading="results.loading"
		:disabled="props.disabled"
		:placeholder="`Search ${props.doctype}`"
	/>
</template>
