/**
 * The dashboard shell (ls_shop/www/dashboard.py) drops the session language and the direction
 * frappe resolved for it on `window`, so no screen has to guess which way the merchant reads.
 *
 * The language cannot change without a round trip to the server, so these are read once rather
 * than kept reactive - switching language reloads the shell, the way frappe's own desk does.
 */
function bootValue<Value>(key: string, fallback: Value): Value {
	const booted = (window as unknown as Record<string, unknown>)[key]
	return typeof booted === typeof fallback ? (booted as Value) : fallback
}

const language = bootValue("lang", "en")
const isRtl = bootValue("is_rtl", false)
const direction: "rtl" | "ltr" = isRtl ? "rtl" : "ltr"

export function useLocale() {
	return { language, isRtl, direction }
}

/**
 * frappe-ui components ship Tailwind `rtl:` variants that only fire under a `dir` on an ancestor,
 * so the mirroring for the whole shell hangs off this one attribute rather than per-component flags.
 */
export function applyDocumentDirection() {
	document.documentElement.dir = direction
	document.documentElement.lang = language
}
