<script setup lang="ts">
import NavInspector from "@/components/navigation/NavInspector.vue"
import NavPreview from "@/components/navigation/NavPreview.vue"
import NavTree from "@/components/navigation/NavTree.vue"
import { useNavMenu } from "@/composables/useNavMenu"
import type { MenuNode } from "@/types"
import {
	Breadcrumbs,
	Button,
	Dropdown,
	LoadingText,
	dialog,
	toast,
	useCall,
} from "frappe-ui"
import { computed, onMounted } from "vue"

const { menu, selected, selectedName, loading, load, call, mutate } =
	useNavMenu()

const itemGroups = useCall<{ name: string }[]>({
	url: "/api/v2/document/Item Group",
	params: {
		fields: JSON.stringify(["name"]),
		limit: 200,
		order_by: "name asc",
	},
})

const itemGroupOptions = computed(() =>
	(itemGroups.data ?? []).map((row) => ({ label: row.name, value: row.name })),
)

onMounted(load)

function addEntry(parent = "") {
	dialog.prompt({
		title: parent ? "Add an entry inside" : "Add a menu section",
		fields: [
			{
				name: "display_name",
				label: "Menu label",
				placeholder: "Shoes",
				required: true,
			},
		],
		confirmLabel: "Add",
		onConfirm: async ({ values }) => {
			await mutate("add_node", { parent, display_name: values.display_name })
		},
	})
}

function importGroups() {
	// Import lands under whatever is selected, so an owner can pull a supplier's category
	// tree into one section rather than always at the top level.
	const parent = selectedName.value ?? ""
	dialog.prompt({
		title: "Build the menu from item groups",
		message: parent
			? `Entries will be added inside "${selected.value?.label}".`
			: "Entries will be added as new top-level sections.",
		fields: [
			{
				name: "item_group",
				label: "Item group",
				type: "combobox",
				options: itemGroupOptions.value,
				required: true,
				description:
					"The group and everything under it, as far as the menu depth allows.",
			},
		],
		confirmLabel: "Import",
		onConfirm: async ({ values }) => {
			const before = countEntries(menu.value)
			await mutate("import_from_item_group", {
				item_group: values.item_group,
				parent,
			})
			const added = countEntries(menu.value) - before
			toast.success(
				added
					? `Added ${added} menu ${added === 1 ? "entry" : "entries"}`
					: "Nothing new to add",
			)
		},
	})
}

function countEntries(nodes: MenuNode[]): number {
	return nodes.reduce(
		(total, node) => total + 1 + countEntries(node.children),
		0,
	)
}

async function removeEntry(node: MenuNode) {
	const preview = await call<{ label: string; count: number }>(
		"get_delete_preview",
		{
			name: node.name,
		},
	)

	dialog.danger({
		title: `Delete "${preview.label}"?`,
		message: preview.count
			? `This also removes ${preview.count} ${preview.count === 1 ? "entry" : "entries"} nested inside it. Products are not deleted.`
			: "Products are not deleted - only this menu entry.",
		onConfirm: async () => {
			await mutate("delete_node", { name: node.name })
			toast.success("Menu entry deleted")
		},
	})
}

async function clearMenu() {
	const preview = await call<{ count: number }>("get_delete_all_preview")

	dialog.danger({
		title: "Delete the whole menu?",
		message: `All ${preview.count} entries are removed and shoppers lose the navigation until you build it again. Products are not deleted.`,
		confirmLabel: "Delete everything",
		onConfirm: async () => {
			await mutate("delete_all_nodes")
			toast.success("Menu cleared")
		},
	})
}

async function toggleVisible(node: MenuNode) {
	await mutate("set_visibility", {
		name: node.name,
		visible: node.visible ? 0 : 1,
	})
}

async function onMove(payload: {
	node: MenuNode
	parent: string
	index: number
	siblings: MenuNode[]
	crossedParent: boolean
}) {
	// Landing in a different list is a re-parent; staying put is only a change of order. They
	// are different endpoints because moving a branch has to revalidate depth and rebuild the
	// nested set, and reordering never does.
	if (payload.crossedParent) {
		await mutate("move_node", {
			name: payload.node.name,
			to_parent: payload.parent,
			target_index: payload.index,
		})
		return
	}

	await mutate("reorder_nodes", {
		parent: payload.parent,
		ordered_names: payload.siblings.map((node) => node.name),
	})
}

const menuActions = computed(() => [
	{
		label: "Import from item groups",
		icon: "download",
		onClick: importGroups,
	},
	{
		group: "Danger",
		items: [
			{
				label: "Delete whole menu",
				icon: "trash-2",
				theme: "red" as const,
				onClick: clearMenu,
			},
		],
	},
])
</script>

<template>
	<div class="flex h-full flex-col bg-surface-base">
		<header
			class="flex min-h-12 items-center justify-between border-b border-outline-gray-1 px-3 sm:px-5"
		>
			<Breadcrumbs :items="[{ label: 'Navigation', route: { name: 'Navigation' } }]" />
			<div class="flex items-center gap-2">
				<Dropdown :options="menuActions">
					<Button icon-left="lucide-ellipsis" label="Actions" />
				</Dropdown>
				<Button
					variant="solid"
					theme="gray"
					icon-left="lucide-plus"
					label="Add section"
					@click="addEntry('')"
				/>
			</div>
		</header>

		<div class="flex min-h-0 flex-1">
			<div class="flex w-80 shrink-0 flex-col border-r border-outline-gray-1">
				<div class="min-h-0 flex-1 overflow-y-auto px-2 py-3">
					<LoadingText v-if="loading && !menu.length" />

					<div v-else-if="!menu.length" class="px-3 py-10 text-center">
						<p class="text-base text-ink-gray-6">No menu yet</p>
						<p class="mt-1 text-p-sm text-ink-gray-5">
							Add a section, or build one from your item groups.
						</p>
						<Button
							class="mt-4"
							variant="subtle"
							theme="gray"
							label="Import from item groups"
							@click="importGroups"
						/>
					</div>

					<NavTree
						v-else
						:items="menu"
						@move="onMove"
						@add="addEntry"
						@remove="removeEntry"
						@toggle-visible="toggleVisible"
					/>
				</div>
			</div>

			<div class="flex w-96 shrink-0 flex-col border-r border-outline-gray-1">
				<NavInspector @remove="removeEntry" />
			</div>

			<div class="min-w-0 flex-1">
				<NavPreview />
			</div>
		</div>
	</div>
</template>
