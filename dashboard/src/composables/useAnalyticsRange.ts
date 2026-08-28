import type { AnalyticsRangeParams } from "@/types"
import { formatShortDate } from "@/utils/format"
import { useCall } from "frappe-ui"
import { computed, ref, watch } from "vue"

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

// Module state, not per-caller state: every widget on the page reads the one range control,
// so switching a preset refetches the whole page rather than the widget that owns the tabs.
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
		: `${formatShortDate(fromDate.value)} – ${formatShortDate(toDate.value)}`,
)

export function useAnalyticsRange() {
	return { preset, fromDate, toDate, rangeParams, rangeCaption }
}

/** The page's Refresh button: every widget reloads, whatever call it owns. */
export function refreshAnalytics() {
	refreshToken.value += 1
}

/**
 * Widgets whose params did not change still have to reload on a manual refresh - `useCall`
 * only refetches when its params do, and the range has not moved.
 */
export function onAnalyticsRefresh(reload: () => void) {
	watch(refreshToken, () => reload())
}

export type AnalyticsReportParams = Record<string, string | number>

/**
 * One report endpoint behind one analytics widget: the call, its place in the page's refresh,
 * and the three shapes every widget hands its panel.
 *
 * `params` is the whole param set, not an addition to the range - `get_live_view` and
 * `get_tracking_health` take no window at all, and sending them one would refetch them every
 * time the reader moved the range.
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
		error: computed(() => report.error?.message ?? null),
		reload,
	}
}
