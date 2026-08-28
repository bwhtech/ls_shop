/**
 * Frappe prefixes every thrown message with its exception class, so a shop owner reading a toast
 * sees "ValidationError: Display name is required." rather than the sentence someone wrote for them.
 * The class name is for a traceback, not for the person trying to save a menu entry.
 */
export function errorMessage(
	error: { message?: string } | null | undefined,
	fallback = "Something went wrong",
) {
	const message = error?.message?.replace(/^\s*[A-Za-z]*Error:\s*/, "").trim()
	return message || fallback
}
