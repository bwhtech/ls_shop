import type {
	BadgeTheme,
	BadgeVariant,
	OrderState,
	ProductRow,
	ProductSize,
} from "@/types"

/** One place that decides how a price range reads, so the list and the detail agree. */
export function formatPriceRange(rates: (number | null)[]) {
	const values = rates.filter(
		(rate): rate is number => rate !== null && rate !== undefined,
	)
	if (!values.length) return "No price"

	const low = Math.min(...values)
	const high = Math.max(...values)
	return low === high ? String(low) : `${low} – ${high}`
}

export function formatRowPrice(product: ProductRow) {
	return formatPriceRange([product.price_from, product.price_to])
}

export function sumStock(sizes: ProductSize[]) {
	return sizes.reduce((total, size) => total + (size.stock ?? 0), 0)
}

/** Status themes live in one map rather than being re-derived at each call site. */
export function publishTheme(publishedCount: number) {
	return publishedCount ? "green" : "gray"
}

/**
 * One badge per rung of the fulfilment ladder, keyed by the stage key the API returns rather than
 * by its English label, so every order badge in the app agrees and translation cannot break it.
 *
 * Badge ships six themes for nine stages, so the ladder is separated on the theme x variant grid:
 * within one hue, `outline` reads lighter than `subtle`, which reads lighter than `solid`. Hue
 * carries the meaning - gray/amber before anything leaves the shelf, violet while the warehouse
 * works, blue once goods are moving, green only for the terminal success, red for the two states
 * that need attention - and every (theme, variant) pair is used once, so no two stages look alike.
 */
const orderStateBadges: Record<
	string,
	{ theme: BadgeTheme; variant: BadgeVariant; icon: string }
> = {
	to_fulfil: { theme: "amber", variant: "subtle", icon: "lucide-inbox" },
	delivery_note_drafted: {
		theme: "gray",
		variant: "subtle",
		icon: "lucide-file-text",
	},
	packed: { theme: "violet", variant: "subtle", icon: "lucide-archive" },
	partly_fulfilled: { theme: "blue", variant: "outline", icon: "lucide-split" },
	fulfilled: { theme: "blue", variant: "subtle", icon: "lucide-check-check" },
	shipped: { theme: "blue", variant: "solid", icon: "lucide-truck" },
	delivered: { theme: "green", variant: "solid", icon: "lucide-circle-check" },
	returned: { theme: "red", variant: "subtle", icon: "lucide-undo-2" },
	cancelled: { theme: "red", variant: "solid", icon: "lucide-circle-x" },
}

const unknownOrderStateBadge = {
	theme: "gray" as BadgeTheme,
	variant: "outline" as BadgeVariant,
	icon: "lucide-circle-dashed",
}

export function orderStateBadge(state: OrderState) {
	return orderStateBadges[state.key] ?? unknownOrderStateBadge
}

export function availabilityTheme(availability: string): BadgeTheme {
	const themes: Record<string, BadgeTheme> = {
		"Out of stock": "red",
		Low: "amber",
		"In stock": "green",
	}
	return themes[availability] ?? "gray"
}

/**
 * Money is rendered in the store's own currency, which only the API knows.
 *
 * `compact` shortens the figure for a KPI tile or an axis tick, where the full
 * grouping would not fit - it is the same function so no call site is tempted to
 * assemble a price out of a code and a number.
 */
export function formatMoney(amount: number, currency: string, compact = false) {
	try {
		return new Intl.NumberFormat(undefined, {
			style: "currency",
			currency,
			currencyDisplay: "narrowSymbol",
			notation: compact ? "compact" : "standard",
			maximumFractionDigits: compact ? 1 : undefined,
		}).format(amount)
	} catch {
		// An unset or unrecognised currency code makes Intl throw; the figure still has to render.
		return `${currency} ${amount.toFixed(2)}`
	}
}

/** Counts read as plain numbers until they get long enough to need shortening. */
export function formatCount(value: number) {
	return new Intl.NumberFormat(undefined, {
		notation: Math.abs(value) >= 10000 ? "compact" : "standard",
		maximumFractionDigits: 1,
	}).format(value)
}

/** Every rate the analytics API returns is already a percentage, to one decimal. */
export function formatPercent(value: number) {
	return `${value.toFixed(1)}%`
}

/** A timestamp that has to carry the time of day, e.g. when a cart was last touched. */
export function formatDateTime(value: string) {
	const parsed = new Date(value)
	if (Number.isNaN(parsed.getTime())) return value
	return new Intl.DateTimeFormat(undefined, {
		day: "numeric",
		month: "short",
		hour: "numeric",
		minute: "2-digit",
	}).format(parsed)
}

/** Short, readable dates for the overview's compact rows - the full date is on the detail screen. */
export function formatShortDate(value: string) {
	const parsed = new Date(value)
	if (Number.isNaN(parsed.getTime())) return value
	return new Intl.DateTimeFormat(undefined, {
		day: "numeric",
		month: "short",
		year: "numeric",
	}).format(parsed)
}

/**
 * ListView puts a right-aligned column's cell in a block-level wrapper that still carries
 * `justify-end`, which does nothing outside a flex box - so the value has to right-align itself or
 * it drifts left, out from under its own header.
 */
export function cellAlignClass(align?: string) {
	return align === "right" || align === "end" ? "block w-full text-right" : ""
}
