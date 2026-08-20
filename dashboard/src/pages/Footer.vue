<script setup lang="ts">
import FooterLinkDialog from "@/components/footer/FooterLinkDialog.vue"
import FooterPreview from "@/components/footer/FooterPreview.vue"
import { useFooter } from "@/composables/useFooter"
import type { FooterLink, FooterSection } from "@/types"
import { useStorage } from "@vueuse/core"
import {
	Badge,
	Breadcrumbs,
	Button,
	Dropdown,
	LoadingText,
	PageHeader,
	ScrollArea,
	Tooltip,
	dialog,
	toast,
} from "frappe-ui"
import { onMounted, ref } from "vue"
import Draggable from "vuedraggable"

const { sections, pages, previewToken, loading, load, mutate, reordered } =
	useFooter()

onMounted(load)

const previewCollapsed = useStorage("ls-shop-footer-preview-collapsed", false)
const linkDialogOpen = ref(false)
const linkDialogSection = ref<FooterSection | null>(null)
const linkDialogLink = ref<FooterLink | null>(null)

/** A drag on the board is already applied to the local lists, so the server is told the result. */
async function onColumnDrop() {
	await mutate("reorder_sections", {
		ordered_names: sections.value.map((section) => section.name),
	})
}

type DragEndEvent = {
	from: HTMLElement
	to: HTMLElement
	item: HTMLElement
	newIndex: number
}

async function onLinkDrop(event: DragEndEvent) {
	const fromSection = event.from.dataset.section
	const toSection = event.to.dataset.section
	const linkRowName = event.item.dataset.name
	if (!fromSection || !toSection || !linkRowName) return

	if (fromSection === toSection) {
		await reorderLinks(fromSection)
		return
	}

	// `move_link` unlinks and re-inserts in one call, so the two columns never disagree about
	// which one owns the row mid-move.
	await mutate("move_link", {
		from_section: fromSection,
		to_section: toSection,
		link_row_name: linkRowName,
		target_index: event.newIndex,
	})
}

function columnOf(name: string) {
	return sections.value.find((section) => section.name === name)
}

async function reorderLinks(sectionName: string) {
	const column = columnOf(sectionName)
	if (!column) return
	await mutate("reorder_links", {
		section_name: sectionName,
		ordered_row_names: column.links.map((link) => link.name),
	})
}

/**
 * Menu-driven equivalents of the drags. Dragging is a pointer-only gesture, so every move the
 * board offers also has to be reachable from a card's or column's menu.
 */
async function moveLinkWithinColumn(
	section: FooterSection,
	linkIndex: number,
	offset: number,
) {
	await mutate("reorder_links", {
		section_name: section.name,
		ordered_row_names: reordered(
			section.links.map((link) => link.name),
			linkIndex,
			linkIndex + offset,
		),
	})
}

async function moveLinkToColumn(
	section: FooterSection,
	link: FooterLink,
	columnIndex: number,
	offset: number,
) {
	const target = sections.value[columnIndex + offset]
	if (!target) return
	await mutate("move_link", {
		from_section: section.name,
		to_section: target.name,
		link_row_name: link.name,
		// Appended rather than kept at the same row: the target column is a different length,
		// so the "same position" the owner sees would not survive the move.
		target_index: target.links.length,
	})
	toast.success(`Moved to ${target.title}`)
}

async function moveSection(columnIndex: number, offset: number) {
	await mutate("reorder_sections", {
		ordered_names: reordered(
			sections.value.map((section) => section.name),
			columnIndex,
			columnIndex + offset,
		),
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

function renameSection(section: FooterSection) {
	dialog.prompt({
		title: "Rename column",
		fields: [
			{
				name: "title",
				label: "Column title",
				defaultValue: section.title,
				required: true,
			},
		],
		confirmLabel: "Rename",
		onConfirm: async ({ values }) => {
			await mutate("rename_section", {
				old_name: section.name,
				new_name: values.title,
			})
			toast.success("Column renamed")
		},
	})
}

function removeSection(section: FooterSection) {
	const count = section.links.length
	dialog.danger({
		title: `Delete "${section.title}"?`,
		message: count
			? `The ${count} ${count === 1 ? "link" : "links"} in this column go with it. Pages are not deleted.`
			: "Pages are not deleted - only this footer column.",
		confirmLabel: "Delete column",
		onConfirm: async () => {
			await mutate("delete_section", { name: section.name })
			toast.success("Column deleted")
		},
	})
}

function removeLink(section: FooterSection, link: FooterLink) {
	dialog.danger({
		title: `Remove "${link.link_label}"?`,
		message: "The page it points at is not deleted - only this footer link.",
		confirmLabel: "Remove link",
		onConfirm: async () => {
			await mutate("delete_link", {
				section_name: section.name,
				link_row_name: link.name,
			})
			toast.success("Link removed")
		},
	})
}

function openLinkDialog(
	section: FooterSection,
	link: FooterLink | null = null,
) {
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

async function toggleSection(section: FooterSection) {
	await mutate("set_section_enabled", {
		name: section.name,
		enabled: section.enabled ? 0 : 1,
	})
}

async function toggleLink(section: FooterSection, link: FooterLink) {
	await mutate("set_link_enabled", {
		section_name: section.name,
		link_row_name: link.name,
		enabled: link.enabled ? 0 : 1,
	})
}

function columnActions(section: FooterSection, columnIndex: number) {
	return [
		{
			label: "Add link",
			icon: "plus",
			onClick: () => openLinkDialog(section),
		},
		{
			label: "Rename",
			icon: "pencil",
			onClick: () => renameSection(section),
		},
		{
			label: "Move left",
			icon: "arrow-left",
			disabled: columnIndex === 0,
			onClick: () => moveSection(columnIndex, -1),
		},
		{
			label: "Move right",
			icon: "arrow-right",
			disabled: columnIndex === sections.value.length - 1,
			onClick: () => moveSection(columnIndex, 1),
		},
		{
			label: section.enabled ? "Hide from footer" : "Show in footer",
			icon: section.enabled ? "eye-off" : "eye",
			onClick: () => toggleSection(section),
		},
		{
			group: "Danger",
			items: [
				{
					label: "Delete column",
					icon: "trash-2",
					theme: "red" as const,
					onClick: () => removeSection(section),
				},
			],
		},
	]
}

function linkActions(
	section: FooterSection,
	columnIndex: number,
	link: FooterLink,
	linkIndex: number,
) {
	return [
		{
			label: "Edit",
			icon: "pencil",
			onClick: () => openLinkDialog(section, link),
		},
		{
			label: "Move up",
			icon: "arrow-up",
			disabled: linkIndex === 0,
			onClick: () => moveLinkWithinColumn(section, linkIndex, -1),
		},
		{
			label: "Move down",
			icon: "arrow-down",
			disabled: linkIndex === section.links.length - 1,
			onClick: () => moveLinkWithinColumn(section, linkIndex, 1),
		},
		{
			label: "Move to previous column",
			icon: "arrow-left",
			disabled: columnIndex === 0,
			onClick: () => moveLinkToColumn(section, link, columnIndex, -1),
		},
		{
			label: "Move to next column",
			icon: "arrow-right",
			disabled: columnIndex === sections.value.length - 1,
			onClick: () => moveLinkToColumn(section, link, columnIndex, 1),
		},
		{
			label: link.enabled ? "Hide from footer" : "Show in footer",
			icon: link.enabled ? "eye-off" : "eye",
			onClick: () => toggleLink(section, link),
		},
		{
			group: "Danger",
			items: [
				{
					label: "Remove link",
					icon: "trash-2",
					theme: "red" as const,
					onClick: () => removeLink(section, link),
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

		<ScrollArea class="min-h-0 flex-1" viewport-class="px-3 py-3 sm:px-5">
			<LoadingText v-if="loading && !sections.length" />

			<div v-else-if="!sections.length" class="px-3 py-16 text-center">
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

			<Draggable
				v-else
				:list="sections"
				item-key="name"
				handle=".footer-column-handle"
				class="flex items-start gap-3"
				@end="onColumnDrop"
			>
				<template #item="{ element: section, index: columnIndex }">
					<div
						class="flex w-72 shrink-0 flex-col rounded-lg border border-outline-gray-1 bg-surface-gray-1"
					>
						<div class="flex items-center gap-2 px-2 py-2">
							<Tooltip text="Drag to reorder columns">
								<button
									type="button"
									class="footer-column-handle cursor-grab text-ink-gray-4 hover:text-ink-gray-6 active:cursor-grabbing"
									aria-label="Drag to reorder column"
								>
									<span class="lucide-grip-vertical size-4 block" aria-hidden="true" />
								</button>
							</Tooltip>

							<span
								class="min-w-0 flex-1 truncate text-base font-medium"
								:class="section.enabled ? 'text-ink-gray-8' : 'text-ink-gray-4'"
							>
								{{ section.title }}
							</span>

							<Badge
								v-if="!section.enabled"
								variant="subtle"
								theme="orange"
								label="Hidden"
							/>
							<span class="shrink-0 text-sm text-ink-gray-5">
								{{ section.links.length }}
							</span>

							<Tooltip text="Add a link">
								<Button
									variant="ghost"
									class="!size-5 shrink-0"
									aria-label="Add a link to this column"
									@click="openLinkDialog(section)"
								>
									<template #icon>
										<span class="lucide-plus size-4 text-ink-gray-5" aria-hidden="true" />
									</template>
								</Button>
							</Tooltip>

							<Dropdown :options="columnActions(section, columnIndex)">
								<Button variant="ghost" class="!size-5 shrink-0" aria-label="Column actions">
									<template #icon>
										<span class="lucide-ellipsis size-4 text-ink-gray-5" aria-hidden="true" />
									</template>
								</Button>
							</Dropdown>
						</div>

						<Draggable
							:list="section.links"
							group="footer-links"
							item-key="name"
							:data-section="section.name"
							class="flex min-h-16 flex-col gap-2 px-2 pb-2"
							@end="onLinkDrop"
						>
							<template #item="{ element: link, index: linkIndex }">
								<div
									:data-name="link.name"
									class="group flex cursor-grab items-start gap-2 rounded-md border border-outline-gray-1 bg-surface-base px-2 py-2 shadow-sm active:cursor-grabbing"
								>
									<button
										type="button"
										class="min-w-0 flex-1 text-left"
										@click="openLinkDialog(section, link)"
									>
										<span
											class="block truncate text-base"
											:class="link.enabled ? 'text-ink-gray-8' : 'text-ink-gray-4'"
										>
											{{ link.link_label }}
										</span>
										<span class="mt-0.5 block truncate text-sm text-ink-gray-5">
											{{ link.link_url }}
										</span>
									</button>

									<div class="flex shrink-0 items-center gap-1">
										<Badge
											v-if="!link.enabled"
											variant="subtle"
											theme="orange"
											label="Hidden"
										/>
										<Dropdown
											:options="linkActions(section, columnIndex, link, linkIndex)"
										>
											<Button variant="ghost" class="!size-5" aria-label="Link actions">
												<template #icon>
													<span class="lucide-ellipsis size-4 text-ink-gray-5" aria-hidden="true" />
												</template>
											</Button>
										</Dropdown>
									</div>
								</div>
							</template>
						</Draggable>

						<div class="px-2 pb-2">
							<Button
								class="w-full"
								variant="ghost"
								theme="gray"
								icon-left="lucide-plus"
								label="Add link"
								@click="openLinkDialog(section)"
							/>
						</div>
					</div>
				</template>
			</Draggable>
		</ScrollArea>

		<FooterPreview v-model:collapsed="previewCollapsed" :token="previewToken" />

		<FooterLinkDialog
			v-model:open="linkDialogOpen"
			:section="linkDialogSection"
			:link="linkDialogLink"
			:pages="pages"
			:submit="saveLink"
		/>
	</div>
</template>
