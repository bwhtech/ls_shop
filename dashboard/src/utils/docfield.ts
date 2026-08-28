/**
 * The docfield vocabulary shared by every screen that renders a doctype's fields from its
 * metadata — the Advanced settings tab and the integration credential forms.
 */

/** As much of a docfield as any of our render paths reads. */
export type DocField = {
	fieldname: string
	label: string
	fieldtype: string
	options: string | null
	description?: string | null
	required?: boolean
	/** Set by the API on a field whose stored value is never sent back to the browser. */
	is_secret?: boolean
	is_set?: boolean
}

export type DocFieldValue = string | number | boolean | null

export const TEXTAREA_FIELDTYPES = [
	"Small Text",
	"Text",
	"Long Text",
	"Text Editor",
	"Code",
	"JSON",
]

export const NUMBER_FIELDTYPES = ["Int", "Float", "Currency", "Percent"]

export function isSecret(field: DocField) {
	return Boolean(field.is_secret) || field.fieldtype === "Password"
}

/** Data fields carry their input hint in `options` (Email / URL / Phone). */
export function textInputType(field: DocField) {
	const hint = (field.options ?? "").toLowerCase()
	if (hint === "email") return "email"
	if (hint === "url") return "url"
	if (hint === "phone") return "tel"
	return "text"
}

export function selectOptions(field: DocField) {
	return (field.options ?? "")
		.split("\n")
		.map((option) => ({ label: option, value: option }))
}

/** Docfield descriptions are authored as HTML; a form row only has room for their text. */
export function plainText(value: string | null | undefined) {
	if (!value) return undefined
	return value.replace(/<[^>]*>/g, "").trim() || undefined
}
