import type { Dayjs } from "dayjs"
import { dayjs } from "frappe-ui"

import type {
	BadgeTheme,
	BadgeVariant,
	OrderState,
	ProductRow,
	ProductSize,
} from "@/types"

/** One place that decides how a price range reads, so the list and the detail agree. */
export function formatPriceRange(
	rates: (number | null)[],
	printRate: (rate: number) => string = String,
) {
	const values = rates.filter(
		(rate): rate is number => rate !== null && rate !== undefined,
	)
	if (!values.length) return "No price"

	const low = Math.min(...values)
	const high = Math.max(...values)
	return low === high
		? printRate(low)
		: `${printRate(low)} – ${printRate(high)}`
}

export function formatRowPrice(product: ProductRow, currency: string) {
	return formatPriceRange([product.price_from, product.price_to], (rate) =>
		formatMoney(rate, currency),
	)
}

export function sumStock(sizes: ProductSize[]) {
	return sizes.reduce((total, size) => total + (size.stock ?? 0), 0)
}

/** Status themes live in one map rather than being re-derived at each call site. */
export function publishTheme(publishedCount: number) {
	return publishedCount ? "green" : "gray"
}

/**
 * A fraction only earns its place when the product is genuinely part-published;
 * "1 of 1 live" reads as a puzzle rather than a status.
 */
export function publishStatus(publishedCount: number, variantCount: number) {
	if (publishedCount && publishedCount < variantCount) {
		return {
			label: `${publishedCount} of ${variantCount} live`,
			theme: "amber" as BadgeTheme,
		}
	}
	return {
		label: publishedCount ? "Live" : "Not live",
		theme: publishTheme(publishedCount) as BadgeTheme,
	}
}

/**
 * Keyed by the stage key the API returns rather than its English label, so translation cannot break the mapping.
 * Badge ships six themes for ten stages, so the ladder is separated on the theme x variant grid.
 */
const orderStateBadges: Record<
	string,
	{ theme: BadgeTheme; variant: BadgeVariant; icon: string }
> = {
	confirmation_pending: {
		theme: "amber",
		variant: "outline",
		icon: "lucide-clock",
	},
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

export function formatMoney(
	amount: number,
	currency: string,
	compact = false,
	symbol?: string,
) {
	try {
		const formatter = new Intl.NumberFormat(undefined, {
			style: "currency",
			currency,
			currencyDisplay: "narrowSymbol",
			notation: compact ? "compact" : "standard",
			maximumFractionDigits: compact ? 1 : undefined,
		})
		// Intl has no narrow symbol for AED or SAR in a Latin locale and prints the code instead, so the
		// site's own symbol is swapped in where Intl placed the currency.
		if (!symbol) return formatter.format(amount)
		return formatter
			.formatToParts(amount)
			.map((part) => (part.type === "currency" ? symbol : part.value))
			.join("")
	} catch {
		// An unset or unrecognised currency code makes Intl throw; the figure still has to render.
		return `${symbol || currency} ${amount.toFixed(2)}`
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

/**
 * Frappe writes its formats in lowercase tokens (dd-mm-yyyy, HH:mm:ss); dayjs wants the date parts
 * uppercased. Month stays `MM` in both, so only the day and year tokens need lifting.
 */
function toDayjsPattern(frappeFormat: string) {
	return frappeFormat
		.replace(/yyyy/g, "YYYY")
		.replace(/yy(?!YY)/g, "YY")
		.replace(/dd/g, "DD")
		.replace(/mm/g, "MM")
}

/**
 * The dashboard shell (ls_shop/www/dashboard.py) drops the site's formats on `window`, so every screen
 * reads the same site setting instead of each falling back to whatever locale the browser happens to be in.
 */
function bootFormat(key: "date_format" | "time_format", fallback: string) {
	const booted = (window as unknown as Record<string, unknown>)[key]
	return toDayjsPattern(
		typeof booted === "string" && booted ? booted : fallback,
	)
}

/**
 * Chart axis formatters are handed an epoch number, which must not be stringified — dayjs would read
 * the digits as a calendar date. Strings get the space swapped for a T, which Safari insists on.
 */
function validMoment(parsed: Dayjs) {
	return parsed.isValid() ? parsed : null
}

function parseMoment(value: DateInput) {
	if (typeof value === "string")
		return value ? validMoment(dayjs(value.replace(" ", "T"))) : null
	if (typeof value === "number" || value instanceof Date)
		return validMoment(dayjs(value))
	return null
}

/** Column and axis formatters hand their value over as `unknown`, so the narrowing happens here. */
type DateInput = unknown

export const emptyValue = "—"

/** Every date in the dashboard goes through here, so the site's date format is the only one on screen. */
export function formatDate(value: DateInput) {
	const parsed = parseMoment(value)
	if (!parsed) return emptyValue
	return parsed.format(bootFormat("date_format", "yyyy-mm-dd"))
}

/** A timestamp that has to carry the time of day, e.g. when a cart was last touched. */
export function formatDateTime(value: DateInput) {
	const parsed = parseMoment(value)
	if (!parsed) return emptyValue
	return parsed.format(
		`${bootFormat("date_format", "yyyy-mm-dd")} ${bootFormat("time_format", "HH:mm:ss")}`,
	)
}

/**
 * ListView puts a right-aligned cell in a block-level wrapper still carrying `justify-end`, which does nothing
 * outside a flex box - so the value has to right-align itself or it drifts out from under its header.
 */
export function cellAlignClass(align?: string) {
	return align === "right" || align === "end" ? "block w-full text-right" : ""
}
