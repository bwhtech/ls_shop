import type { FooterEditorData, FooterSection } from "@/types"
import { ref } from "vue"
import { createMethodCaller } from "./methodCaller"

const sections = ref<FooterSection[]>([])
const pages = ref<FooterEditorData["pages"]>([])

// The preview frames the rendered storefront footer and cannot be told the columns moved, so every mutation bumps this.
const previewToken = ref(0)

const { attempt, call, loading } = createMethodCaller(
	"/api/v2/method/ls_shop.api.admin.footer.",
)

// A refused read leaves `sections` empty, which reads as "this store has no footer" unless the failure is kept.
const loadError = ref<Error | null>(null)

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
	const { data, error } = await attempt<FooterEditorData>("get_editor_data")
	loadError.value = error
	apply(data)
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
		loadError,
		previewToken,
		loading,
		load,
		mutate,
		reordered,
	}
}
