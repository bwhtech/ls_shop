<script setup lang="ts">
import { useNavMenu } from "@/composables/useNavMenu"
import type { MenuNode } from "@/types"
import { useStorage } from "@vueuse/core"
import { Badge, Button, Dropdown } from "frappe-ui"
import { computed, onBeforeUnmount, ref, watch } from "vue"
import draggable from "vuedraggable"

defineOptions({ name: "NavTree" })

const props = withDefaults(
	defineProps<{
		items: MenuNode[]
		/** Depth of the list itself: 0 is the row of top-level tabs, so it doubles as parent depth. */
		level?: number
		parentName?: string
	}>(),
	{ level: 0, parentName: "" },
)

const emit = defineEmits<{
	move: [
		payload: {
			node: MenuNode
			parent: string
			index: number
			siblings: MenuNode[]
			crossedParent: boolean
		},
	]
	add: [parent: string]
	remove: [node: MenuNode]
	toggleVisible: [node: MenuNode]
}>()

const { selectedName, canNest, maxDepth, dragActive } = useNavMenu()

// Whether a node at this level is allowed to take children at all. Gates the drop zone, so a
// row at the depth cap never offers a target the server would refuse.
const acceptsChildren = computed(() => props.level + 1 < maxDepth.value)

const expanded = useStorage<Record<string, boolean>>("ls-shop-nav-expanded", {})

// vuedraggable mutates the list it is given, so it gets a local copy. While a drag is in flight
// the incoming prop is ignored: the server answers every move with a whole new tree, and
// adopting it mid-gesture yanks the row out from under the pointer.
const rows = ref<MenuNode[]>([...props.items])
let settleTimer: ReturnType<typeof setTimeout> | null = null

watch(
	() => props.items,
	(items) => {
		if (dragActive.value) return
		rows.value = [...items]
	},
)

function isExpanded(name: string) {
	return expanded.value[name] === true
}

function toggle(name: string) {
	expanded.value[name] = !expanded.value[name]
}

function select(node: MenuNode) {
	selectedName.value = node.name
}

function onStart() {
	dragActive.value = true
	if (settleTimer) clearTimeout(settleTimer)
}

function onEnd() {
	if (settleTimer) clearTimeout(settleTimer)
	// The tree arrives from the server a moment after the drop; hold the local copy until then.
	settleTimer = setTimeout(() => {
		dragActive.value = false
		settleTimer = null
	}, 800)
}

// Dragging over a collapsed branch opens it, so its children become reachable without
// dropping first. Desk's editor does the same; without it a collapsed branch is a dead end.
let hoverTimer: ReturnType<typeof setTimeout> | null = null

function onRowDragOver(node: MenuNode) {
	if (!dragActive.value || !node.children.length || isExpanded(node.name))
		return
	if (hoverTimer) return
	hoverTimer = setTimeout(() => {
		expanded.value[node.name] = true
		hoverTimer = null
	}, 500)
}

function onRowDragLeave() {
	if (hoverTimer) clearTimeout(hoverTimer)
	hoverTimer = null
}

/**
 * Sortable's own veto hook. The server caps the menu depth and throws past it, so a drop that
 * would bury a branch too deep is refused while dragging - the row simply will not land there.
 */
function onMove(event: {
	to: HTMLElement
	draggedContext: { element: MenuNode }
}) {
	const targetLevel = Number(event.to.dataset.level ?? 0)
	return canNest(event.draggedContext.element, targetLevel)
}

function onChange(event: {
	added?: { element: MenuNode; newIndex: number }
	moved?: { element: MenuNode; newIndex: number }
}) {
	const change = event.added ?? event.moved
	if (!change) return

	emit("move", {
		node: change.element,
		parent: props.parentName,
		index: change.newIndex,
		siblings: rows.value,
		crossedParent: Boolean(event.added),
	})
}

function options(node: MenuNode) {
	return [
		{
			label: "Add entry inside",
			icon: "corner-down-right",
			onClick: () => emit("add", node.name),
		},
		{
			label: node.visible ? "Hide from menu" : "Show in menu",
			icon: node.visible ? "eye-off" : "eye",
			onClick: () => emit("toggleVisible", node),
		},
		{
			group: "Danger",
			items: [
				{
					label: "Delete",
					icon: "trash-2",
					theme: "red" as const,
					onClick: () => emit("remove", node),
				},
			],
		},
	]
}

onBeforeUnmount(() => {
	if (settleTimer) clearTimeout(settleTimer)
	if (hoverTimer) clearTimeout(hoverTimer)
})
</script>

<template>
	<draggable
		tag="div"
		:list="rows"
		:data-level="level"
		:group="{ name: 'nav-tree' }"
		item-key="name"
		handle=".drag-handle"
		ghost-class="nav-row-ghost"
		:animation="150"
		:move="onMove"
		:class="
			level > 0 && !rows.length
				? 'mb-1 ml-6 rounded border border-dashed border-outline-gray-2 py-3 text-center text-sm text-ink-gray-5'
				: 'min-h-2'
		"
		@start="onStart"
		@end="onEnd"
		@change="onChange"
	>
		<template #item="{ element }">
			<div>
				<div
					class="group flex items-center gap-1.5 rounded py-1.5 pr-1.5 hover:bg-surface-gray-2"
					:class="selectedName === element.name ? 'bg-surface-gray-3' : 'cursor-pointer'"
					:style="{ paddingLeft: `${level * 14 + 6}px` }"
					@click="select(element)"
					@dragover="onRowDragOver(element)"
					@dragleave="onRowDragLeave"
				>
					<Button
						variant="ghost"
						class="drag-handle !size-5 shrink-0 cursor-grab opacity-0 group-hover:opacity-100 active:cursor-grabbing"
						aria-label="Reorder"
						@click.stop
					>
						<template #icon>
							<span class="lucide-grip-vertical size-4 text-ink-gray-4" aria-hidden="true" />
						</template>
					</Button>

					<Button
						v-if="element.children.length"
						variant="ghost"
						class="!size-5 shrink-0"
						:aria-label="isExpanded(element.name) ? 'Collapse' : 'Expand'"
						@click.stop="toggle(element.name)"
					>
						<template #icon>
							<span
								class="lucide-chevron-right size-4 text-ink-gray-5 transition-transform duration-200"
								:class="{ 'rotate-90': isExpanded(element.name) }"
								aria-hidden="true"
							/>
						</template>
					</Button>
					<span v-else class="size-5 shrink-0" />

					<span
						class="truncate text-base"
						:class="element.visible ? 'text-ink-gray-8' : 'text-ink-gray-4'"
					>
						{{ element.label }}
					</span>

					<Badge v-if="!element.visible" variant="subtle" theme="orange" label="Hidden" />

					<!-- Fixed slot on the right so the counts form a column down the tree rather
					     than floating at the end of each label. -->
					<span class="ml-auto w-16 shrink-0 text-right text-sm text-ink-gray-5">
						{{ element.item_groups.length ? `${element.item_groups.length} groups` : "" }}
					</span>

					<span @click.stop>
						<Dropdown :options="options(element)">
							<Button
								variant="ghost"
								class="!size-5 shrink-0 opacity-0 group-hover:opacity-100"
								aria-label="Entry actions"
							>
								<template #icon>
									<span class="lucide-ellipsis size-4 text-ink-gray-5" aria-hidden="true" />
								</template>
							</Button>
						</Dropdown>
					</span>
				</div>

				<div
					v-show="
						element.children.length
							? isExpanded(element.name)
							: dragActive && acceptsChildren
					"
				>
					<NavTree
						:items="element.children"
						:level="level + 1"
						:parent-name="element.name"
						@move="(payload) => emit('move', payload)"
						@add="(parent) => emit('add', parent)"
						@remove="(node) => emit('remove', node)"
						@toggle-visible="(node) => emit('toggleVisible', node)"
					/>
				</div>
			</div>
		</template>
	</draggable>
</template>

<style scoped>
.nav-row-ghost {
	opacity: 0.4;
}
</style>
