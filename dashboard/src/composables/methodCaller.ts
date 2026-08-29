import { toast, useCall } from "frappe-ui"
import { computed, effectScope, ref } from "vue"
import { errorMessage } from "../utils/errors"

/**
 * One call over a mutable url does not work: VueUse aborts the in-flight request and every caller reads the same `data`.
 * Built in a detached scope because the calls outlive whichever component first reached for an endpoint.
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

	/**
	 * Both halves of the outcome - a toast fades, so a screen that must tell a refusal
	 * from a genuinely empty answer needs the error handed back, not only logged.
	 */
	async function attempt<TResponse>(
		method: string,
		params: Record<string, unknown> = {},
	): Promise<{ data: TResponse | null; error: Error | null }> {
		const request = requestFor(method)
		pending.value += 1
		try {
			// `submit` resolves null on a failed request instead of rejecting, so a refusal is read off the call.
			const data = await request.submit(params)
			const error = (request.error as Error | null | undefined) ?? null
			if (error) {
				toast.error(errorMessage(error))
				return { data: null, error }
			}
			return { data: data as TResponse, error: null }
		} finally {
			pending.value -= 1
		}
	}

	/** Resolves to the endpoint's answer, or null when it refused - the reason is toasted here. */
	async function call<TResponse>(
		method: string,
		params: Record<string, unknown> = {},
	): Promise<TResponse | null> {
		const { data } = await attempt<TResponse>(method, params)
		return data
	}

	return { attempt, call, loading: computed(() => pending.value > 0) }
}
