<script setup lang="ts">
import FooterLinkDialog from "@/components/footer/FooterLinkDialog.vue"
import { useFooter } from "@/composables/useFooter"
import type { FooterNode } from "@/types"
import {
	Badge,
	Breadcrumbs,
	Button,
	Dropdown,
	LoadingText,
	PageHeader,
	Tree,
	dialog,
	toast,
} from "frappe-ui"
import type { DropInfo, MoveContext } from "frappe-ui"
import { onMounted, ref } from "vue"

const { sections, pages, nodes, loading, load, mutate, sectionOf, reordered } =
	useFooter()

onMounted(load)

const linkDialogOpen = ref(false)
const linkDialogSection = ref<FooterNode | null>(null)
const linkDialogLink = ref<FooterNode | null>(null)

/**
 * Domain rule for a drop. The footer is exactly two levels deep, so a column stays a column and
 * a link can only ever land inside one - anything else would ask the server for a shape the
 * doctypes cannot hold.
 */
function canDrop({ node, target, position }: MoveContext) {
	const dragged = node as FooterNode
	const onto = target as FooterNode
	if (dragged.kind === "section")
		return onto.kind === "section" && position !== "inside"
	return onto.kind === "section" ? position === "inside" : position !== "inside"
}

async function onDragEnd(info: DropInfo | null) {
	// Null means the drag was cancelled or never landed anywhere valid.
	if (!info) return

	const node = info.node as FooterNode

	if (node.kind === "section") {
		await mutate("reorder_sections", {
			ordered_names: reordered(
				sections.value.map((section) => section.name),
				info.oldIndex,
				info.newIndex,
			),
		})
		return
	}

	const fromSection = sectionOf(info.from)
	const toSection = sectionOf(info.to)
	if (!fromSection || !toSection) return

	if (fromSection === toSection) {
		const column = sections.value.find(
			(section) => section.name === fromSection,
		)
		await mutate("reorder_links", {
			section_name: fromSection,
			ordered_row_names: reordered(
				(column?.links ?? []).map((link) => link.name),
				info.oldIndex,
				info.newIndex,
			),
		})
		return
	}

	// `move_link` unlinks and re-inserts in one call, so the two columns never disagree about
	// which one owns the row mid-move.
	await mutate("move_link", {
		from_section: fromSection,
		to_section: toSection,
		link_row_name: node.name,
		target_index: info.newIndex,
	})
}

function addSection() {
	dialog.prompt({
		title: "Add a footer column",
		fields: [
			{
				name: "title",
				label: "Column title",
				placeholder: "Help",
				required: true,
			},
		],
		confirmLabel: "Add",
		onConfirm: async ({ values }) => {
			await mutate("add_section", { title: values.title })
			toast.success("Column added")
		},
	})
}

function renameSection(node: FooterNode) {
	dialog.prompt({
		title: "Rename column",
		fields: [
			{
				name: "title",
				label: "Column title",
				defaultValue: node.label,
				required: true,
			},
		],
		confirmLabel: "Rename",
		onConfirm: async ({ values }) => {
			await mutate("rename_section", {
				old_name: node.name,
				new_name: values.title,
			})
			toast.success("Column renamed")
		},
	})
}

function removeSection(node: FooterNode) {
	const count = node.children.length
	dialog.danger({
		title: `Delete "${node.label}"?`,
		message: count
			? `The ${count} ${count === 1 ? "link" : "links"} in this column go with it. Pages are not deleted.`
			: "Pages are not deleted - only this footer column.",
		confirmLabel: "Delete column",
		onConfirm: async () => {
			await mutate("delete_section", { name: node.name })
			toast.success("Column deleted")
		},
	})
}

function removeLink(node: FooterNode) {
	dialog.danger({
		title: `Remove "${node.label}"?`,
		message: "The page it points at is not deleted - only this footer link.",
		confirmLabel: "Remove link",
		onConfirm: async () => {
			await mutate("delete_link", {
				section_name: node.section,
				link_row_name: node.name,
			})
			toast.success("Link removed")
		},
	})
}

function openLinkDialog(section: FooterNode, link: FooterNode | null = null) {
	linkDialogSection.value = section
	linkDialogLink.value = link
	linkDialogOpen.value = true
}

async function saveLink({ label, url }: { label: string; url: string }) {
	const section = linkDialogSection.value
	const link = linkDialogLink.value
	if (!section) return

	if (link)
		await mutate("update_link", {
			section_name: section.name,
			link_row_name: link.name,
			label,
			url,
		})
	else await mutate("add_link", { section_name: section.name, label, url })
}

async function toggleEnabled(node: FooterNode) {
	const enabled = node.enabled ? 0 : 1
	if (node.kind === "section")
		await mutate("set_section_enabled", { name: node.name, enabled })
	else
		await mutate("set_link_enabled", {
			section_name: node.section,
			link_row_name: node.name,
			enabled,
		})
}

function editLink(node: FooterNode) {
	const parent = nodes.value.find((section) => section.name === node.section)
	if (parent) openLinkDialog(parent, node)
}

function rowActions(node: FooterNode) {
	const visibility = {
		label: node.enabled ? "Hide from footer" : "Show in footer",
		icon: node.enabled ? "eye-off" : "eye",
		onClick: () => toggleEnabled(node),
	}

	if (node.kind === "section")
		return [
			{ label: "Add link", icon: "plus", onClick: () => openLinkDialog(node) },
			{ label: "Rename", icon: "pencil", onClick: () => renameSection(node) },
			visibility,
			{
				group: "Danger",
				items: [
					{
						label: "Delete column",
						icon: "trash-2",
						theme: "red" as const,
						onClick: () => removeSection(node),
					},
				],
			},
		]

	return [
		{ label: "Edit", icon: "pencil", onClick: () => editLink(node) },
		visibility,
		{
			group: "Danger",
			items: [
				{
					label: "Remove link",
					icon: "trash-2",
					theme: "red" as const,
					onClick: () => removeLink(node),
				},
			],
		},
	]
}
</script>

<template>
	<div class="flex h-full flex-col bg-surface-base">
		<PageHeader>
			<Breadcrumbs :items="[{ label: 'Footer', route: { name: 'Footer' } }]" />
			<Button
				variant="solid"
				theme="gray"
				icon-left="lucide-plus"
				label="Add column"
				@click="addSection"
			/>
		</PageHeader>

		<div class="min-h-0 flex-1 overflow-y-auto px-3 py-3 sm:px-5">
			<LoadingText v-if="loading && !nodes.length" />

			<div v-else-if="!nodes.length" class="px-3 py-16 text-center">
				<p class="text-base text-ink-gray-6">No footer columns yet</p>
				<p class="mt-1 text-p-sm text-ink-gray-5">
					Add a column, then fill it with links to your pages.
				</p>
				<Button
					class="mt-4"
					variant="subtle"
					theme="gray"
					label="Add column"
					@click="addSection"
				/>
			</div>

			<Tree
				v-else
				:nodes="nodes"
				node-key="key"
				draggable
				:move="canDrop"
				@drag-end="onDragEnd"
			>
				<!-- A section is a plain label: renaming lives in its row menu, so a stray click on
				     a column heading cannot start an edit nobody asked for. -->
				<template #item-label="{ node }">
					<span
						v-if="node.kind === 'section'"
						class="min-w-0 flex-1 truncate text-base font-medium"
						:class="node.enabled ? 'text-ink-gray-8' : 'text-ink-gray-4'"
					>
						{{ node.label }}
					</span>
					<button
						v-else
						type="button"
						class="flex min-w-0 flex-1 items-baseline gap-2 text-left"
						@click.stop="editLink(node as FooterNode)"
					>
						<span
							class="shrink-0 truncate text-base"
							:class="node.enabled ? 'text-ink-gray-8' : 'text-ink-gray-4'"
						>
							{{ node.label }}
						</span>
						<span class="truncate text-sm text-ink-gray-5">{{ node.url }}</span>
					</button>
				</template>

				<template #item-suffix="{ node }">
					<div class="flex items-center gap-2">
						<Badge
							v-if="!node.enabled"
							variant="subtle"
							theme="orange"
							label="Hidden"
						/>
						<span class="w-16 shrink-0 text-right text-sm text-ink-gray-5">
							{{
								node.kind === "section"
									? `${node.children.length} ${node.children.length === 1 ? "link" : "links"}`
									: ""
							}}
						</span>
						<span @click.stop>
							<Dropdown :options="rowActions(node as FooterNode)">
								<Button variant="ghost" class="!size-5 shrink-0" aria-label="Row actions">
									<template #icon>
										<span class="lucide-ellipsis size-4 text-ink-gray-5" aria-hidden="true" />
									</template>
								</Button>
							</Dropdown>
						</span>
					</div>
				</template>
			</Tree>
		</div>

		<FooterLinkDialog
			v-model:open="linkDialogOpen"
			:section="linkDialogSection"
			:link="linkDialogLink"
			:pages="pages"
			:submit="saveLink"
		/>
	</div>
</template>
