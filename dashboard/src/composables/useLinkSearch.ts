import { refDebounced } from "@vueuse/core"
import { useCall } from "frappe-ui"
import { computed, ref, watch } from "vue"

/** Server-side search behind a Combobox: the endpoint decides what matches, not the client. */
export function useLinkSearch<TOption>(
	url: string,
	extraParams: () => Record<string, string> = () => ({}),
) {
	const open = ref(false)
	const query = ref("")

	// The combobox keeps the input showing the committed label while it is closed, so a closed
	// picker must not search for its own value - only a query typed into an open popover counts.
	watch(open, (isOpen) => {
		if (isOpen) query.value = ""
	})

	const searchText = refDebounced(
		computed(() => (open.value ? query.value : "")),
		300,
	)

	const results = useCall<TOption[]>({
		url,
		params: () => ({ ...extraParams(), search_text: searchText.value }),
		refetch: true,
	})

	return { open, query, results }
}
