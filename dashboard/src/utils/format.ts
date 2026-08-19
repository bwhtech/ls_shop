import type { ProductRow, ProductSize } from "@/types"

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

/** Order state themes live beside the publish map, so every badge in the app agrees. */
export function orderStateTheme(state: string) {
	return (
		{
			"To fulfil": "orange",
			"Partly fulfilled": "blue",
			Fulfilled: "green",
			Cancelled: "red",
		}[state] ?? "gray"
	)
}

export function availabilityTheme(availability: string) {
	return (
		{ "Out of stock": "red", Low: "orange", "In stock": "green" }[
			availability
		] ?? "gray"
	)
}
