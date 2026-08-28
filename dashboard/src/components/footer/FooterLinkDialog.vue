<script setup lang="ts">
import type { FooterLink, FooterPage, FooterSection } from "@/types"
import { Button, Combobox, Dialog, FormControl, toast } from "frappe-ui"
import { computed, ref, useId, watch } from "vue"

const props = defineProps<{
	/** The column the link belongs to. */
	section: FooterSection | null
	/** The link being edited, or null when adding a new one. */
	link: FooterLink | null
	pages: FooterPage[]
	/** Runs the server call. Resolves false when the server refused it, and the dialog stays open. */
	submit: (payload: { label: string; url: string }) => Promise<boolean>
}>()

const open = defineModel<boolean>("open", { required: true })

// The submit button sits in the dialog's own action row, outside the form. `form` is how HTML
// associates the two, so the browser runs each field's `required` check on click.
const formId = useId()

const SOURCE_OPTIONS = [
	{ label: "Custom URL", value: "url" },
	{ label: "Existing page", value: "page" },
]

const source = ref("url")
const page = ref("")
const label = ref("")
const url = ref("")
const saving = ref(false)

const isEdit = computed(() => Boolean(props.link))

const pageOptions = computed(() =>
	props.pages.map((row) => ({ label: row.name, value: row.name })),
)

// Core `Web Page` routes are relative ("about" -> /about); the storefront's own routes already
// arrive as absolute paths.
function pageUrl(route: string) {
	return route.startsWith("/") ? route : `/${route}`
}

watch(open, (isOpen) => {
	if (!isOpen) return
	// Editing starts on the URL field: the link already has one, and re-picking a page would
	// overwrite a label the owner may have deliberately changed.
	source.value = "url"
	page.value = ""
	label.value = props.link?.link_label ?? ""
	url.value = props.link?.link_url ?? ""
})

watch(page, (name) => {
	const match = props.pages.find((row) => row.name === name)
	if (!match) return
	label.value = match.name
	url.value = pageUrl(match.route)
})

async function save() {
	saving.value = true
	try {
		// A refused save resolves false rather than throwing, so closing the dialog waits on
		// the answer - closing it regardless would throw away what the owner typed.
		const saved = await props.submit({
			label: label.value.trim(),
			url: url.value.trim(),
		})
		if (!saved) return

		open.value = false
		toast.success(isEdit.value ? "Link saved" : "Link added")
	} finally {
		saving.value = false
	}
}
</script>

<template>
	<Dialog v-model:open="open" :title="isEdit ? 'Edit link' : 'Add a link'">
		<template #default>
			<form :id="formId" class="space-y-4" @submit.prevent="save">
				<p v-if="section" class="text-p-base text-ink-gray-7">
					In the {{ section.title }} column.
				</p>
				<FormControl
					v-if="!isEdit"
					v-model="source"
					type="select"
					label="Link source"
					:options="SOURCE_OPTIONS"
					description="Pick a page to fill the label and address in for you."
				/>

				<Combobox
					v-if="source === 'page'"
					v-model="page"
					:options="pageOptions"
					label="Page"
					placeholder="Search pages"
				/>

				<FormControl v-model="label" label="Label" required placeholder="Shipping & returns" />

				<FormControl
					v-model="url"
					label="URL"
					required
					placeholder="/en/products"
					description="Where this link sends shoppers."
				/>

			</form>
		</template>

		<template #actions>
			<Button
				class="w-full"
				type="submit"
				:form="formId"
				variant="solid"
				theme="gray"
				:loading="saving"
				:label="isEdit ? 'Save' : 'Add'"
			/>
		</template>
	</Dialog>
</template>
