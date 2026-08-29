import { refDebounced } from "@vueuse/core"
import { useCall } from "frappe-ui"
import { computed, ref } from "vue"

/** Server-side search behind a Combobox: the endpoint decides what matches, not the client. */
export function useLinkSearch<TOption>(
	url: string,
	extraParams: () => Record<string, string> = () => ({}),
	/** The committed value the trigger is currently displaying, where the caller has one. */
	committedValue: () => string | null | undefined = () => null,
) {
	const open = ref(false)
	const query = ref("")

	// In the combobox's input mode the query IS the value display, so only a genuinely different query counts.
	const searchText = refDebounced(
		computed(() =>
			open.value && query.value !== committedValue() ? query.value : "",
		),
		300,
	)

	const results = useCall<TOption[], Record<string, string>>({
		url,
		params: () => ({ ...extraParams(), search_text: searchText.value }),
		refetch: true,
	})

	return { open, query, results }
}
