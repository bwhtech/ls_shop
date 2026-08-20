import type { BadgeTheme, OrderState, ProductRow, ProductSize } from "@/types"

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
 */
const orderStateBadges: Record<string, { theme: BadgeTheme; icon: string }> = {
	to_fulfil: { theme: "amber", icon: "lucide-inbox" },
	delivery_note_drafted: { theme: "gray", icon: "lucide-file-text" },
	partly_fulfilled: { theme: "blue", icon: "lucide-package-open" },
	fulfilled: { theme: "blue", icon: "lucide-package-check" },
	packed: { theme: "violet", icon: "lucide-package" },
	shipped: { theme: "blue", icon: "lucide-truck" },
	delivered: { theme: "green", icon: "lucide-circle-check" },
	returned: { theme: "amber", icon: "lucide-undo-2" },
	cancelled: { theme: "red", icon: "lucide-circle-x" },
}

const unknownOrderStateBadge = {
	theme: "gray" as BadgeTheme,
	icon: "lucide-circle-dashed",
}

export function orderStateBadge(state: OrderState) {
	return orderStateBadges[state.key] ?? unknownOrderStateBadge
}

export function availabilityTheme(availability: string) {
	return (
		{ "Out of stock": "red", Low: "orange", "In stock": "green" }[
			availability
		] ?? "gray"
	)
}

/** Money is rendered in the store's own currency, which only the API knows. */
export function formatMoney(amount: number, currency: string) {
	try {
		return new Intl.NumberFormat(undefined, {
			style: "currency",
			currency,
			currencyDisplay: "narrowSymbol",
		}).format(amount)
	} catch {
		// An unset or unrecognised currency code makes Intl throw; the figure still has to render.
		return `${currency} ${amount.toFixed(2)}`
	}
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
