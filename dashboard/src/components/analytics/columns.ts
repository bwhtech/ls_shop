import { formatCount, formatMoney, formatPercent } from "@/utils/format"

export type AnalyticsTableColumn<
	TRow extends Record<string, unknown> = Record<string, unknown>,
> = {
	/** Doubles as the slot name, so a cell that needs a badge or a link overrides just that one. */
	key: string
	label: string
	numeric?: boolean
	/** Prints the cell; a column without one prints the raw value. */
	format?: (value: unknown, row: TRow) => string
}

/** The three numeric cells the analytics tables are almost entirely made of. */
export function countColumn<TRow extends Record<string, unknown>>(
	key: string,
	label: string,
): AnalyticsTableColumn<TRow> {
	return {
		key,
		label,
		numeric: true,
		format: (value) => formatCount(Number(value)),
	}
}

export function percentColumn<TRow extends Record<string, unknown>>(
	key: string,
	label: string,
): AnalyticsTableColumn<TRow> {
	return {
		key,
		label,
		numeric: true,
		format: (value) => formatPercent(Number(value)),
	}
}

/** The currency arrives with the overview, so it is read at render time rather than captured. */
export function moneyColumn<TRow extends Record<string, unknown>>(
	key: string,
	label: string,
	currency: () => string,
): AnalyticsTableColumn<TRow> {
	return {
		key,
		label,
		numeric: true,
		format: (value) => formatMoney(Number(value), currency()),
	}
}
