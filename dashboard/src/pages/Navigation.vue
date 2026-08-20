<script setup lang="ts">
import NavInspector from "@/components/navigation/NavInspector.vue"
import { useNavMenu } from "@/composables/useNavMenu"
import type { MenuNode } from "@/types"
import {
	Badge,
	Breadcrumbs,
	Button,
	Dropdown,
	LoadingText,
	Tree,
	dialog,
	toast,
	useCall,
} from "frappe-ui"
import { computed, onMounted } from "vue"

const {
	menu,
	selected,
	selectedName,
	loading,
	load,
	call,
	mutate,
	depthOf,
	canNest,
} = useNavMenu()

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

/**
 * Domain rule for a drop. Tree already rejects dropping onto itself or into its own descendant,
 * so this only has to answer the depth question the server would otherwise throw on.
 */
function canDrop({
	node,
	target,
	position,
}: { node: MenuNode; target: MenuNode; position: string }) {
	const parentDepth =
		position === "inside" ? depthOf(target.name) : depthOf(target.name) - 1
	return canNest(node, parentDepth)
}

async function onDragEnd(
	info: { node: MenuNode; to: string | null; newIndex: number } | null,
) {
	// Null means the drag was cancelled or never landed anywhere valid.
	if (!info) return

	// `move_node` reparents and positions in one call, so a reorder within one parent and a
	// move across parents are the same request - `to` is simply unchanged in the first case.
	await mutate("move_node", {
		name: info.node.name,
		to_parent: info.to ?? "",
		target_index: info.newIndex,
	})
}

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

function countEntries(nodes: MenuNode[]): number {
	return nodes.reduce(
		(total, node) => total + 1 + countEntries(node.children),
		0,
	)
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

function rowActions(node: MenuNode) {
	return [
		{
			label: "Add entry inside",
			icon: "corner-down-right",
			onClick: () => addEntry(node.name),
		},
		{
			label: node.visible ? "Hide from menu" : "Show in menu",
			icon: node.visible ? "eye-off" : "eye",
			onClick: () => toggleVisible(node),
		},
		{
			group: "Danger",
			items: [
				{
					label: "Delete",
					icon: "trash-2",
					theme: "red" as const,
					onClick: () => removeEntry(node),
				},
			],
		},
	]
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
			<div class="min-h-0 flex-1 overflow-y-auto px-3 py-3 sm:px-5">
				<LoadingText v-if="loading && !menu.length" />

				<div v-else-if="!menu.length" class="px-3 py-16 text-center">
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

				<Tree
					v-else
					:nodes="menu"
					node-key="name"
					draggable
					:move="canDrop"
					@drag-end="onDragEnd"
				>
					<template #item-label="{ node }">
						<button
							type="button"
							class="min-w-0 flex-1 truncate text-left text-base"
							:class="[
								node.visible ? 'text-ink-gray-8' : 'text-ink-gray-4',
								selectedName === node.name ? 'font-medium' : '',
							]"
							@click.stop="selectedName = node.name"
						>
							{{ node.label }}
						</button>
					</template>

					<template #item-suffix="{ node }">
						<div class="flex items-center gap-2">
							<Badge v-if="!node.visible" variant="subtle" theme="orange" label="Hidden" />
							<span class="w-16 shrink-0 text-right text-sm text-ink-gray-5">
								{{ node.item_groups.length ? `${node.item_groups.length} groups` : "" }}
							</span>
							<span @click.stop>
								<Dropdown :options="rowActions(node)">
									<Button
										variant="ghost"
										class="!size-5 shrink-0"
										aria-label="Entry actions"
									>
										<template #icon>
											<span
												class="lucide-ellipsis size-4 text-ink-gray-5"
												aria-hidden="true"
											/>
										</template>
									</Button>
								</Dropdown>
							</span>
						</div>
					</template>
				</Tree>
			</div>

			<div class="flex w-96 shrink-0 flex-col border-l border-outline-gray-1">
				<NavInspector @remove="removeEntry" />
			</div>
		</div>
	</div>
</template>
