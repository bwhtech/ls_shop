import type { FooterEditorData, FooterSection } from "@/types"
import { ref } from "vue"
import { createMethodCaller } from "./methodCaller"

const sections = ref<FooterSection[]>([])
const pages = ref<FooterEditorData["pages"]>([])

// The preview frames the rendered storefront footer, so it cannot be told the columns moved -
// it has to fetch again. Every mutation bumps this.
const previewToken = ref(0)

const { call, loading } = createMethodCaller(
	"/api/v2/method/ls_shop.api.admin.footer.",
)

function apply(data: FooterEditorData | null) {
	if (!data) return

	sections.value = data.columns ?? []
	pages.value = data.pages ?? []
}

/** Run a mutation and adopt the footer it returns, or null when the server refused it. */
async function mutate(name: string, params: Record<string, unknown> = {}) {
	const data = await call<FooterEditorData>(name, params)
	if (!data) return null
	apply(data)
	previewToken.value += 1
	return data
}

async function load() {
	apply(await call<FooterEditorData>("get_editor_data"))
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
		previewToken,
		loading,
		load,
		mutate,
		reordered,
	}
}
