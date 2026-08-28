import { refDebounced } from "@vueuse/core"
import { useCall } from "frappe-ui"
import { computed, ref, shallowRef, watch } from "vue"

/**
 * A searchable, paged list screen.
 *
 * `useCall` serialises params into the url for a GET and refetches when the url changes, so the
 * search term is debounced rather than the request: a hand-rolled timer on top of `refetch` fires
 * once per keystroke and again when it elapses.
 *
 * "Load more" fetches the next page and appends it, so the rows already read stay where they are
 * and the request never asks for a window the endpoint would cap.
 */
export function usePagedList<TResponse extends { total: number }, TRow>(
	url: string,
	pageLength: number,
	selectRows: (data: TResponse) => TRow[],
	filters: () => Record<string, string> = () => ({}),
) {
	const search = ref("")
	const searchText = refDebounced(search, 300)
	const start = ref(0)
	const rows = shallowRef<TRow[]>([])

	const query = computed(() => ({ ...filters(), search: searchText.value }))

	// A new search or filter starts from the first page again. Sync, so the offset is already
	// back at zero by the time the request url recomputes and refetches.
	watch(
		query,
		() => {
			start.value = 0
		},
		{ flush: "sync" },
	)

	const request = useCall<TResponse, Record<string, string>>({
		url,
		params: () => ({
			...query.value,
			start: String(start.value),
			page_length: String(pageLength),
		}),
		refetch: true,
		onSuccess: (data) => {
			const page = selectRows(data)
			rows.value = start.value ? [...rows.value, ...page] : page
		},
	})

	const total = computed(() => request.data?.total ?? 0)
	const hasMore = computed(() => rows.value.length < total.value)

	function loadMore() {
		start.value += pageLength
	}

	/**
	 * Read the list again from the first page. Re-running a grown window as it stands would append
	 * the same page a second time, so a reload always goes back to the start.
	 */
	function reload() {
		if (start.value === 0) {
			request.reload()
			return
		}
		start.value = 0
	}

	return { search, request, rows, total, hasMore, loadMore, reload }
}
