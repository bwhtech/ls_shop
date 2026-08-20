import type { FooterEditorData, FooterSection } from "@/types"
import { toast, useCall } from "frappe-ui"
import { computed, ref } from "vue"

const METHOD_PREFIX = "/api/v2/method/ls_shop.api.admin.footer."

const sections = ref<FooterSection[]>([])
const pages = ref<FooterEditorData["pages"]>([])

const method = ref("get_editor_data")

const request = useCall<FooterEditorData, Record<string, unknown>>({
	url: computed(() => METHOD_PREFIX + method.value),
	method: "POST",
	immediate: false,
	onError: (error) => toast.error(error.message),
})

function apply(data: FooterEditorData | undefined) {
	if (!data) return

	sections.value = data.columns ?? []
	pages.value = data.pages ?? []
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
		loading: computed(() => request.loading),
		load,
		mutate,
		reordered,
	}
}
