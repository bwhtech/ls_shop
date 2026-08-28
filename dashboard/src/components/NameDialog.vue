<script setup lang="ts">
import { Button, Dialog, FormControl } from "frappe-ui"
import { ref, useId, watch } from "vue"

const props = defineProps<{
	title: string
	/** Label above the single field. */
	label: string
	placeholder?: string
	/** Label on the submit button. */
	confirmLabel: string
	/** Line above the field, for the context the name lands in. */
	message?: string
	/** Runs the server call. Resolves false when the server refused it, and the dialog stays open. */
	submit: (name: string) => Promise<boolean>
}>()

const open = defineModel<boolean>("open", { required: true })

// The submit button sits in the dialog's own action row, outside the form. `form` is how HTML
// associates the two, so the browser runs the field's `required` check on click.
const formId = useId()

const name = ref("")
const saving = ref(false)

watch(open, (isOpen) => {
	if (isOpen) name.value = ""
})

async function save() {
	saving.value = true
	try {
		// A refusal resolves false rather than throwing, so closing waits on the answer -
		// closing regardless would throw away what the owner typed.
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
