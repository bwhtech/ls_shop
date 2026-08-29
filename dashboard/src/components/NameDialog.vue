<script setup lang="ts">
import { Button, Dialog, FormControl } from "frappe-ui"
import { ref, useId, watch } from "vue"

const props = defineProps<{
	title: string
	label: string
	placeholder?: string
	confirmLabel: string
	message?: string
	submit: (name: string) => Promise<boolean>
}>()

const open = defineModel<boolean>("open", { required: true })

// The submit button sits outside the form, so `form` is what makes the browser run the field's `required` check.
const formId = useId()

const name = ref("")
const saving = ref(false)

watch(open, (isOpen) => {
	if (isOpen) name.value = ""
})

async function save() {
	saving.value = true
	try {
		if (await props.submit(name.value.trim())) open.value = false
	} finally {
		saving.value = false
	}
}
</script>

<template>
	<Dialog v-model:open="open" :title="title">
		<template #default>
			<form :id="formId" class="space-y-4" @submit.prevent="save">
				<p v-if="message" class="text-p-base text-ink-gray-7">{{ message }}</p>
				<FormControl
					v-model="name"
					:label="label"
					:placeholder="placeholder"
					required
				/>
			</form>
		</template>

		<template #actions>
			<div class="flex flex-row-reverse gap-2">
				<Button
					type="submit"
					:form="formId"
					variant="solid"
					theme="gray"
					:loading="saving"
					:label="confirmLabel"
				/>
				<Button
					variant="outline"
					label="Cancel"
					:disabled="saving"
					@click="open = false"
				/>
			</div>
		</template>
	</Dialog>
</template>
