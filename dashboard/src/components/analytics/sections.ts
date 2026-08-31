/**
 * The analytics group's sub-views. One list feeds the sub-nav and the command palette,
 * so a section can never be reachable from one and invisible to the other.
 */
export type AnalyticsSection = {
	label: string
	/** Route name, as declared in router.ts. */
	route: string
}

export const analyticsSections: AnalyticsSection[] = [
	{ label: "Overview", route: "Analytics" },
]
