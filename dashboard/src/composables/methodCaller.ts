import { toast, useCall } from "frappe-ui"
import { computed, effectScope, ref } from "vue"
import { errorMessage } from "../utils/errors"

/**
 * A `call(method, params)` over one module of whitelisted methods.
 *
 * Every method gets its own `useCall`. One call multiplexed over a mutable url does not work:
 * VueUse aborts the request in flight as soon as the next one starts, and every caller resolves
 * from the same `data` - so one endpoint's answer lands in another endpoint's caller.
 *
 * The calls are built in a detached scope because they outlive whichever component first reached
 * for an endpoint; created inside that component's scope they would stop updating on its unmount.
 */
export function createMethodCaller(methodPrefix: string) {
	const scope = effectScope(true)
	const requests = new Map<string, ReturnType<typeof createRequest>>()
	const pending = ref(0)

	function createRequest(method: string) {
		return useCall<unknown, Record<string, unknown>>({
			url: methodPrefix + method,
			method: "POST",
			immediate: false,
		})
	}

	function requestFor(method: string) {
		let request = requests.get(method)
		if (!request) {
			request = scope.run(() => createRequest(method))
			if (!request) throw new Error(`Could not prepare a request for ${method}`)
			requests.set(method, request)
		}
		return request
	}

	/** Resolves to the endpoint's answer, or null when it refused - the reason is toasted here. */
	async function call<TResponse>(
		method: string,
		params: Record<string, unknown> = {},
	): Promise<TResponse | null> {
		const request = requestFor(method)
		pending.value += 1
		try {
			// `submit` resolves null on a failed request instead of rejecting, so a refusal is
			// read off the call rather than caught.
			const data = await request.submit(params)
			if (request.error) {
				toast.error(errorMessage(request.error))
				return null
			}
			return data as TResponse
		} finally {
			pending.value -= 1
		}
	}

	return { call, loading: computed(() => pending.value > 0) }
}
