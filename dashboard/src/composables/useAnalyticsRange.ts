import type { AnalyticsRangeParams } from "@/types"
import { formatDate } from "@/utils/format"
import { useCall } from "frappe-ui"
import { computed, ref, watch } from "vue"
import { errorMessage } from "../utils/errors"

export const METHOD_PREFIX = "/api/v2/method/ls_shop.api.analytics_dashboard."

export type AnalyticsRangePreset = "today" | "7" | "30" | "90"

export const analyticsRangeOptions: {
	label: string
	value: AnalyticsRangePreset
}[] = [
	{ label: "Today", value: "today" },
	{ label: "7D", value: "7" },
	{ label: "30D", value: "30" },
	{ label: "90D", value: "90" },
]

/** Both ends are inclusive server-side, so a 7D window is today plus the six before it. */
const presetDays: Record<AnalyticsRangePreset, number> = {
	today: 1,
	"7": 7,
	"30": 30,
	"90": 90,
}

const preset = ref<AnalyticsRangePreset>("30")
const refreshToken = ref(0)

/** `toISOString()` would shift an evening date back a day anywhere behind UTC. */
function toApiDate(date: Date) {
	const year = date.getFullYear()
	const month = String(date.getMonth() + 1).padStart(2, "0")
	const day = String(date.getDate()).padStart(2, "0")
	return `${year}-${month}-${day}`
}

const toDate = computed(() => toApiDate(new Date()))

const fromDate = computed(() => {
	const start = new Date()
	start.setDate(start.getDate() - (presetDays[preset.value] - 1))
	return toApiDate(start)
})

const rangeParams = computed<AnalyticsRangeParams>(() => ({
	from_date: fromDate.value,
	to_date: toDate.value,
}))

const rangeCaption = computed(() =>
	preset.value === "today"
		? "Today"
		: `${formatDate(fromDate.value)} – ${formatDate(toDate.value)}`,
)

export function useAnalyticsRange() {
	return { preset, fromDate, toDate, rangeParams, rangeCaption }
}

/** The page's Refresh button: every widget reloads, whatever call it owns. */
export function refreshAnalytics() {
	refreshToken.value += 1
}

/** `useCall` only refetches when its params change, so a manual refresh has to reload widgets whose params did not. */
export function onAnalyticsRefresh(reload: () => void) {
	watch(refreshToken, () => reload())
}

export type AnalyticsReportParams = Record<string, string | number>

/**
 * `params` is the whole param set, not an addition to the range: `get_live_view` and `get_tracking_health`
 * take no window, and sending them one would refetch them every time the reader moved the range.
 */
export function useAnalyticsReport<TData>(
	method: string,
	params: () => AnalyticsReportParams = () => rangeParams.value,
) {
	const report = useCall<TData, AnalyticsReportParams>({
		url: `${METHOD_PREFIX}${method}`,
		params,
		refetch: true,
	})

	function reload() {
		report.reload()
	}

	onAnalyticsRefresh(reload)

	return {
		data: computed(() => report.data),
		// A reload keeps the previous reading on screen rather than flashing the skeleton again.
		loading: computed(() => report.loading && !report.data),
		error: computed(() => (report.error ? errorMessage(report.error) : null)),
		reload,
	}
}
