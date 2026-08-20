import type { MenuNode } from "@/types"
import { toast, useCall } from "frappe-ui"
import { computed, ref } from "vue"

interface EditorData {
	menu: MenuNode[]
	max_depth: number
	preview_url: string
}

const METHOD_PREFIX = "/api/v2/method/ls_shop.api.admin.navigation."

const menu = ref<MenuNode[]>([])
const maxDepth = ref(0)
const previewUrl = ref("/")
const selectedName = ref<string | null>(null)

// The preview frames the real storefront, so it cannot be told the menu changed - it has to be
// asked to render again. Every mutation bumps this and the pane reloads off the new value.
const previewToken = ref(0)

const method = ref("get_editor_data")

const request = useCall<EditorData, Record<string, unknown>>({
	url: computed(() => METHOD_PREFIX + method.value),
	method: "POST",
	immediate: false,
	onError: (error) => toast.error(error.message),
})

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

/**
 * Whether a node can be dropped under a parent at the given depth.
 *
 * The server throws past `max_depth`, so the tree checks first and refuses the drop rather than
 * animating a move that is about to be rejected and snapped back.
 */
function canNest(node: MenuNode, parentDepth: number): boolean {
	return parentDepth + 1 + subtreeHeight(node) <= maxDepth.value
}

function apply(data: EditorData | undefined) {
	if (!data) return
	menu.value = data.menu ?? []
	if (data.max_depth) maxDepth.value = data.max_depth
	if (data.preview_url) previewUrl.value = data.preview_url

	// A deleted node must not stay selected - the inspector would render a stale copy of a
	// row that is no longer in the tree.
	if (selectedName.value && !findNode(selectedName.value))
		selectedName.value = null
}

async function call<T = EditorData>(
	name: string,
	params: Record<string, unknown> = {},
) {
	method.value = name
	const data = (await request.submit(params)) as T
	return data
}

/** Run a mutation and adopt the tree it returns. */
async function mutate(name: string, params: Record<string, unknown> = {}) {
	const data = await call(name, params)
	apply(data as EditorData)
	previewToken.value += 1
	return data
}

async function load() {
	apply(await call("get_editor_data"))
}

export function useNavMenu() {
	return {
		menu,
		maxDepth,
		previewUrl,
		previewToken,
		selectedName,
		selected,
		loading: computed(() => request.loading),
		load,
		call,
		mutate,
		findNode,
		depthOf,
		canNest,
	}
}
