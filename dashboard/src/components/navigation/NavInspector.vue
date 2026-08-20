<script setup lang="ts">
import { useLinkSearch } from "@/composables/useLinkSearch"
import { useNavMenu } from "@/composables/useNavMenu"
import type { MenuLinkType, MenuNode } from "@/types"
import {
	Button,
	Combobox,
	ErrorMessage,
	FormControl,
	MultiSelect,
	Switch,
	toast,
} from "frappe-ui"
import { computed, reactive, ref, watch } from "vue"

const { selected, mutate } = useNavMenu()

const emit = defineEmits<{ remove: [node: MenuNode] }>()

const LINK_TYPES = [
	{ label: "Nothing — heading only", value: "" },
	{ label: "Item groups", value: "Item Group" },
	{ label: "Brand", value: "Brand" },
	{ label: "Custom URL", value: "URL" },
]

const form = reactive({
	label: "",
	route_slug: "",
	link_type: "" as MenuLinkType,
	item_groups: [] as string[],
	brand: "",
	url: "",
	icon: "",
	meta_title: "",
	meta_description: "",
	noindex: false,
})

const saving = ref(false)
const error = ref("")

const isRoot = computed(() => Boolean(selected.value && !selected.value.parent))

// Reload the form whenever a different entry is picked. Watching `name` rather than the node
// keeps the fields still while the tree is replaced by a save that did not change selection.
watch(
	() => selected.value?.name,
	() => {
		const node = selected.value
		error.value = ""
		if (!node) return
		form.label = node.label
		form.route_slug = node.route_slug
		form.link_type = node.link_type
		form.item_groups = [...node.item_groups]
		form.brand = node.brand
		form.url = node.url
		form.icon = node.icon
		form.meta_title = node.meta_title
		form.meta_description = node.meta_description
		form.noindex = Boolean(node.noindex)
	},
	{ immediate: true },
)

type LinkOption = { label: string; value: string }

const LINK_OPTIONS_URL =
	"/api/v2/method/ls_shop.api.admin.navigation.get_link_options"

// The same server-side search the settings pickers use: the endpoint decides what matches, not
// the client, so a large catalog stays searchable rather than being capped at a first page.
const itemGroupSearch = useLinkSearch<LinkOption>(LINK_OPTIONS_URL, () => ({
	doctype: "Item Group",
}))
const brandSearch = useLinkSearch<LinkOption>(LINK_OPTIONS_URL, () => ({
	doctype: "Brand",
}))

// Already-linked values are merged into the options: a search only returns what matches the
// current query, and without this a saved group vanishes from the control as soon as someone types.
function withSelected(options: LinkOption[], selected: string[]) {
	const merged = new Map(options.map((option) => [option.value, option]))
	for (const value of selected) {
		if (value && !merged.has(value)) merged.set(value, { label: value, value })
	}
	return [...merged.values()]
}

const itemGroupOptions = computed(() =>
	withSelected(itemGroupSearch.results.data ?? [], form.item_groups),
)

const brandOptions = computed(() =>
	withSelected(brandSearch.results.data ?? [], [form.brand]),
)

function linkTarget() {
	if (form.link_type === "Item Group") return form.item_groups
	if (form.link_type === "Brand") return form.brand
	if (form.link_type === "URL") return form.url
	return null
}

async function save() {
	const node = selected.value
	if (!node) return

	error.value = ""
	saving.value = true
	try {
		await mutate("update_node", {
			name: node.name,
			display_name: form.label,
			link_type: form.link_type,
			link_target: linkTarget(),
			// The server rejects a blank slug outright, so an untouched optional slug is left
			// out of the payload rather than sent as "" and thrown back.
			route_slug: form.route_slug || undefined,
			icon: form.icon,
			meta_title: form.meta_title,
			meta_description: form.meta_description,
			noindex: form.noindex ? 1 : 0,
		})
		toast.success("Menu entry saved")
	} catch (exception) {
		error.value = (exception as Error).message
	} finally {
		saving.value = false
	}
}
</script>

<template>
	<div v-if="!selected" class="grid h-full place-items-center px-5 text-center">
		<div>
			<p class="text-base text-ink-gray-6">Pick an entry to edit it</p>
			<p class="mt-1 text-p-sm text-ink-gray-5">
				Drag entries to reorder them, or drop one onto another to nest it.
			</p>
		</div>
	</div>

	<div v-else class="flex h-full flex-col">
		<div class="flex min-h-12 items-center justify-between border-b border-outline-gray-1 px-5">
			<span class="truncate text-base font-medium text-ink-gray-8">{{ selected.label }}</span>
			<Button
				variant="ghost"
				theme="red"
				icon-left="lucide-trash-2"
				label="Delete"
				@click="emit('remove', selected)"
			/>
		</div>

		<div class="min-h-0 flex-1 overflow-y-auto px-5 pb-40 pt-5">
			<div class="space-y-4">
				<FormControl v-model="form.label" label="Menu label" required />

				<FormControl
					v-model="form.route_slug"
					label="URL slug"
					:required="isRoot"
					:description="
						isRoot
							? 'Used in the storefront address for this section.'
							: 'Optional. Top-level sections need one; entries below them do not.'
					"
				/>

				<FormControl
					v-model="form.link_type"
					type="select"
					label="Links to"
					:options="LINK_TYPES"
					description="Leave as a heading to show a label that is not clickable."
				/>

				<MultiSelect
					v-if="form.link_type === 'Item Group'"
					v-model="form.item_groups"
					v-model:open="itemGroupSearch.open.value"
					v-model:query="itemGroupSearch.query.value"
					:options="itemGroupOptions"
					:filterable="false"
					:loading="itemGroupSearch.results.loading"
					label="Item groups"
					description="Products from every group listed here appear together under this entry."
					placeholder="Search item groups"
				/>

				<Combobox
					v-else-if="form.link_type === 'Brand'"
					v-model="form.brand"
					v-model:open="brandSearch.open.value"
					v-model:query="brandSearch.query.value"
					:options="brandOptions"
					:filterable="false"
					:loading="brandSearch.results.loading"
					label="Brand"
					placeholder="Search brands"
				/>

				<FormControl
					v-else-if="form.link_type === 'URL'"
					v-model="form.url"
					label="URL"
					description="Where this entry sends shoppers."
				/>

				<FormControl
					v-model="form.icon"
					label="Icon"
					description="Optional icon name or CSS class."
				/>
			</div>

			<div class="mt-8 space-y-4">
				<h3 class="text-base font-medium text-ink-gray-8">Search engine listing</h3>

				<FormControl
					v-model="form.meta_title"
					label="Page title"
					description="Defaults to the menu label and your store name."
				/>
				<FormControl
					v-model="form.meta_description"
					type="textarea"
					label="Description"
					description="Shown under the title in search results."
				/>
				<Switch
					v-model="form.noindex"
					label="Hide from search engines"
					description="Asks crawlers not to list this page."
				/>
			</div>

			<ErrorMessage v-if="error" class="mt-4" :message="error" />
		</div>

		<div class="flex justify-end border-t border-outline-gray-1 px-5 py-3">
			<Button
				variant="solid"
				theme="gray"
				label="Save"
				:loading="saving"
				@click="save"
			/>
		</div>
	</div>
</template>
