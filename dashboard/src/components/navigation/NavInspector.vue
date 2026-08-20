<script setup lang="ts">
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
	useCall,
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

const itemGroupQuery = ref("")
const brandQuery = ref("")

/** Name-only lookup against a doctype, narrowed by whatever the picker has been typed into. */
function nameSearchParams(query: string) {
	return {
		fields: JSON.stringify(["name"]),
		filters: JSON.stringify(query ? [["name", "like", `%${query}%`]] : []),
		limit: 20,
		order_by: "name asc",
	}
}

const itemGroups = useCall<{ name: string }[]>({
	url: "/api/v2/document/Item Group",
	params: () => nameSearchParams(itemGroupQuery.value),
	refetch: true,
})

const brands = useCall<{ name: string }[]>({
	url: "/api/v2/document/Brand",
	params: () => nameSearchParams(brandQuery.value),
	refetch: true,
})

// The picker must be able to show what is already linked, not just what the current search
// returned, or saved groups vanish from the trigger the moment someone types.
const itemGroupOptions = computed(() => {
	const names = new Set([
		...form.item_groups,
		...(itemGroups.data ?? []).map((row) => row.name),
	])
	return [...names].map((name) => ({ label: name, value: name }))
})

const brandOptions = computed(() => {
	const names = new Set(
		[form.brand, ...(brands.data ?? []).map((row) => row.name)].filter(Boolean),
	)
	return [...names].map((name) => ({ label: name, value: name }))
})

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
					v-model:query="itemGroupQuery"
					:options="itemGroupOptions"
					label="Item groups"
					description="Products from every group listed here appear together under this entry."
					placeholder="Search item groups"
				/>

				<Combobox
					v-else-if="form.link_type === 'Brand'"
					v-model="form.brand"
					v-model:query="brandQuery"
					:options="brandOptions"
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
