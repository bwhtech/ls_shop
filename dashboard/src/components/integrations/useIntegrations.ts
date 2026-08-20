import { toast, useCall } from "frappe-ui"
import { computed } from "vue"

export type IntegrationValue = string | number | boolean | null

/** One editable docfield of an integration's settings doctype, as the API describes it. */
export type IntegrationField = {
	fieldname: string
	label: string
	fieldtype: string
	options: string | null
	description: string | null
	required: boolean
	value: IntegrationValue
	is_secret: boolean
	is_set: boolean
}

/** A Section Break's worth of fields. */
export type IntegrationGroup = {
	label: string
	fields: IntegrationField[]
}

export type Integration = {
	slug: string
	label: string
	blurb: string
	settings_doctype: string
	available: boolean
	enabled: boolean
	configured: boolean
	missing: string[]
	webhook_url: string | null
	docs_url: string | null
	groups: IntegrationGroup[]
}

export type IntegrationValues = Record<string, IntegrationValue>

export type SaveIntegrationParams = {
	slug: string
	enabled: boolean
	values: IntegrationValues
}

/** Frappe's v2 API prefixes the exception class onto its message; the shop owner only needs the sentence. */
export function integrationErrorMessage(error: Error | null | undefined) {
	if (!error?.message) return "Could not save this integration"
	return error.message.replace(/^\s*[A-Za-z]*Error:\s*/, "")
}

/**
 * Load/save cycle for one family of integrations (payment gateways, shipping providers, …).
 * Everything provider-specific lives behind the two urls, so a second screen is a second pair.
 */
export function useIntegrations(urls: { listUrl: string; saveUrl: string }) {
	const list = useCall<Integration[]>({ url: urls.listUrl })

	const save = useCall<Integration, SaveIntegrationParams>({
		url: urls.saveUrl,
		method: "POST",
		immediate: false,
	})

	const integrations = computed(() => list.data ?? [])

	/** Resolves to the saved integration, or null when the backend refused it — the reason stays on `save.error`. */
	async function saveIntegration(params: SaveIntegrationParams) {
		const saved = await save.submit(params)
		if (save.error || !saved) return null
		toast.success(`${saved.label} saved`)
		await list.reload()
		return saved
	}

	return { list, integrations, save, saveIntegration }
}
