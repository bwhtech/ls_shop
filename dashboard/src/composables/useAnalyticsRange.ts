import { formatShortDate } from "@/utils/format"
import { computed, ref, watch } from "vue"

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

const rangeParams = computed(() => ({
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
