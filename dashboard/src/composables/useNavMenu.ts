import type { MenuNode } from "@/types"
import { computed, ref } from "vue"
import { createMethodCaller } from "./methodCaller"

interface EditorData {
	menu: MenuNode[]
	max_depth: number
}

const menu = ref<MenuNode[]>([])
const maxDepth = ref(0)
const selectedName = ref<string | null>(null)

const { attempt, call, loading } = createMethodCaller(
	"/api/v2/method/ls_shop.api.admin.navigation.",
)

// A refused read leaves `menu` empty, which reads as "this store has no menu" unless the failure is kept.
const loadError = ref<Error | null>(null)

function walk(
	nodes: MenuNode[],
	visit: (node: MenuNode, depth: number) => void,
	depth = 1,
) {
	for (const node of nodes) {
		visit(node, depth)
		walk(node.children, visit, depth + 1)
	}
}

function findNode(
	name: string | null,
	nodes: MenuNode[] = menu.value,
): MenuNode | null {
	if (!name) return null
	for (const node of nodes) {
		if (node.name === name) return node
		const found = findNode(name, node.children)
		if (found) return found
	}
	return null
}

const selected = computed(() => findNode(selectedName.value))

/** Levels hanging below a node - 0 for a leaf, so a node with children only is 1. */
function subtreeHeight(node: MenuNode): number {
	if (!node.children.length) return 0
	return 1 + Math.max(...node.children.map(subtreeHeight))
}

/** Depth a node currently sits at, counting a top-level tab as 1. */
function depthOf(name: string): number {
	let depth = 0
	walk(menu.value, (node, nodeDepth) => {
		if (node.name === name) depth = nodeDepth
	})
	return depth
}

/** The server throws past `max_depth`, so the tree refuses the drop rather than animating a move about to be snapped back. */
function canNest(node: MenuNode, parentDepth: number): boolean {
	return parentDepth + 1 + subtreeHeight(node) <= maxDepth.value
}

/**
 * `Tree` keeps each node's open state on the node itself and every mutation replaces the whole tree,
 * so without this, moving one entry collapses the branch the owner is working in.
 */
function rememberExpansion() {
	const state = new Map<string, boolean>()
	walk(menu.value, (node) => state.set(node.name, node.expanded !== false))
	return state
}

function applyExpansion(
	nodes: MenuNode[],
	state: Map<string, boolean>,
	depth = 1,
) {
	for (const node of nodes) {
		node.expanded = state.get(node.name) ?? depth === 1
		applyExpansion(node.children, state, depth + 1)
	}
}

function apply(data: EditorData | null) {
	if (!data?.menu) return

	const expansion = rememberExpansion()
	const nodes = data.menu
	applyExpansion(nodes, expansion)
	menu.value = nodes
	if (data.max_depth) maxDepth.value = data.max_depth

	// A deleted node must not stay selected - the inspector would render a stale copy of a row no longer in the tree.
	if (selectedName.value && !findNode(selectedName.value))
		selectedName.value = null
}

/** The nodes from the top level down to `name`, or none when it is not in the tree. */
function pathTo(name: string, nodes: MenuNode[] = menu.value): MenuNode[] {
	for (const node of nodes) {
		if (node.name === name) return [node]
		const below = pathTo(name, node.children)
		if (below.length) return [node, ...below]
	}
	return []
}

/**
 * `revealUnder` opens the branch a row was added to or moved into: the refresh otherwise restores that branch's
 * remembered collapsed state, so the change lands on the server yet looks like nothing happened.
 */
async function mutate(
	method: string,
	params: Record<string, unknown> = {},
	revealUnder = "",
) {
	const data = await call<EditorData>(method, params)
	if (!data) return null
	apply(data)
	for (const node of pathTo(revealUnder)) node.expanded = true
	// Every menu change funnels through here, so this is the one place the storefront preview is told it is stale.
	revision.value += 1
	return data
}

const revision = ref(0)

async function load() {
	const { data, error } = await attempt<EditorData>("get_editor_data")
	loadError.value = error
	apply(data)
}

export function useNavMenu() {
	return {
		menu,
		maxDepth,
		loadError,
		revision,
		selectedName,
		selected,
		loading,
		load,
		call,
		mutate,
		findNode,
		depthOf,
		canNest,
	}
}
