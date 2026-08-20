import type { FooterEditorData, FooterNode, FooterSection } from "@/types"
import { toast, useCall } from "frappe-ui"
import { computed, ref } from "vue"

const METHOD_PREFIX = "/api/v2/method/ls_shop.api.admin.footer."

const SECTION_PREFIX = "section:"
const LINK_PREFIX = "link:"

const sections = ref<FooterSection[]>([])
const pages = ref<FooterEditorData["pages"]>([])
const nodes = ref<FooterNode[]>([])

const method = ref("get_editor_data")

const request = useCall<FooterEditorData, Record<string, unknown>>({
	url: computed(() => METHOD_PREFIX + method.value),
	method: "POST",
	immediate: false,
	onError: (error) => toast.error(error.message),
})

function sectionKey(name: string) {
	return SECTION_PREFIX + name
}

/** The section a `DropInfo.from`/`to` key belongs to, or null for the root level. */
function sectionOf(key: string | number | null): string | null {
	if (typeof key !== "string" || !key.startsWith(SECTION_PREFIX)) return null
	return key.slice(SECTION_PREFIX.length)
}

function toNodes(columns: FooterSection[]): FooterNode[] {
	return columns.map((column) => ({
		key: sectionKey(column.name),
		kind: "section" as const,
		name: column.name,
		label: column.title,
		section: "",
		url: "",
		enabled: column.enabled,
		children: column.links.map((link) => ({
			key: LINK_PREFIX + link.name,
			kind: "link" as const,
			name: link.name,
			label: link.link_label,
			section: column.name,
			url: link.link_url,
			enabled: link.enabled,
			children: [],
		})),
	}))
}

/**
 * Carry expansion across a refresh.
 *
 * `Tree` keeps each column's open state on the node itself, and every mutation replaces the
 * whole forest with the server's answer - so without this, adding one link would collapse the
 * column the owner is working in.
 */
function applyExpansion(next: FooterNode[]) {
	const wasCollapsed = new Set(
		nodes.value
			.filter((node) => node.expanded === false)
			.map((node) => node.key),
	)
	for (const node of next) node.expanded = !wasCollapsed.has(node.key)
}

function apply(data: FooterEditorData | undefined) {
	if (!data) return

	sections.value = data.columns ?? []
	pages.value = data.pages ?? []

	const next = toNodes(sections.value)
	applyExpansion(next)
	nodes.value = next
}

async function call(name: string, params: Record<string, unknown> = {}) {
	method.value = name
	return (await request.submit(params)) as FooterEditorData
}

/** Run a mutation and adopt the footer it returns. */
async function mutate(name: string, params: Record<string, unknown> = {}) {
	apply(await call(name, params))
}

async function load() {
	apply(await call("get_editor_data"))
}

/** The order a list ends up in after `oldIndex` is lifted out and dropped at `newIndex`. */
function reordered(names: string[], oldIndex: number, newIndex: number) {
	const next = [...names]
	const [moved] = next.splice(oldIndex, 1)
	next.splice(newIndex, 0, moved)
	return next
}

export function useFooter() {
	return {
		sections,
		pages,
		nodes,
		loading: computed(() => request.loading),
		load,
		mutate,
		sectionOf,
		reordered,
	}
}
