<script setup lang="ts">
import type { FooterLink, FooterPage, FooterSection } from "@/types"
import { Combobox, Dialog, ErrorMessage, FormControl, toast } from "frappe-ui"
import { computed, ref, watch } from "vue"

const props = defineProps<{
	/** The column the link belongs to. */
	section: FooterSection | null
	/** The link being edited, or null when adding a new one. */
	link: FooterLink | null
	pages: FooterPage[]
	/** Runs the server call. Awaited, so the dialog only closes once the save lands. */
	submit: (payload: { label: string; url: string }) => Promise<void>
}>()

const open = defineModel<boolean>("open", { required: true })

const SOURCE_OPTIONS = [
	{ label: "Custom URL", value: "url" },
	{ label: "Existing page", value: "page" },
]

const source = ref("url")
const page = ref("")
const label = ref("")
const url = ref("")
const error = ref("")

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
	error.value = ""
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
	error.value = ""
	if (!label.value.trim() || !url.value.trim()) {
		error.value = "A link needs both a label and a URL."
		return
	}

	try {
		await props.submit({ label: label.value, url: url.value })
		open.value = false
		toast.success(isEdit.value ? "Link saved" : "Link added")
	} catch (exception) {
		error.value = (exception as Error).message
	}
}
</script>

<template>
	<Dialog
		v-model:open="open"
		:title="isEdit ? 'Edit link' : 'Add a link'"
		:actions="[
			{
				label: isEdit ? 'Save' : 'Add',
				variant: 'solid',
				theme: 'gray',
				onClick: save,
			},
		]"
	>
		<template #default>
			<div class="space-y-4">
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

				<ErrorMessage v-if="error" :message="error" />
			</div>
		</template>
	</Dialog>
</template>
