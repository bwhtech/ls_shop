/**
 * Brand plates for the integration cards. One house treatment for every provider — a rounded
 * brand-coloured tile carrying the provider's own logo — so a row of them reads as a set.
 *
 * Stripe, Telr and Tabby are wordmark brands, so their wordmark IS their logo. Razorpay locks a
 * glyph up with its wordmark, so it gets the glyph (path from Simple Icons, CC0).
 * `svg` is the inner markup of a 112x40 plate; the tile itself is drawn by IntegrationLogo.
 */
export type IntegrationLogo = {
	svg: string
	background: string
}

const WORDMARK_ATTRS =
	'x="56" y="24.5" text-anchor="middle" font-family="Inter, ui-sans-serif, system-ui, sans-serif" font-weight="600" letter-spacing="-0.3"'

function wordmark(text: string, color: string, size = 15) {
	return `<text ${WORDMARK_ATTRS} font-size="${size}" fill="${color}">${text}</text>`
}

function accentBar(color: string) {
	return `<rect x="42" y="29" width="28" height="2.5" rx="1.25" fill="${color}" />`
}

/** A 24x24 brand glyph placed on the plate, scaled to `size` and anchored at its top-left. */
function mark(path: string, color: string, x: number, y: number, size: number) {
	const scale = size / 24
	return `<g transform="translate(${x} ${y}) scale(${scale})"><path d="${path}" fill="${color}" /></g>`
}

/** Left-anchored companion to `wordmark`, for a glyph-plus-wordmark lockup. */
function lockupWordmark(text: string, color: string, x: number, size: number) {
	return `<text x="${x}" y="24.5" text-anchor="start" font-family="Inter, ui-sans-serif, system-ui, sans-serif" font-weight="600" letter-spacing="-0.3" font-size="${size}" fill="${color}">${text}</text>`
}

// Simple Icons (CC0). Razorpay's own lockup is this glyph followed by the wordmark.
const RAZORPAY_GLYPH =
	"M22.436 0l-11.91 7.773-1.174 4.276 6.625-4.297L11.65 24h4.391l6.395-24zM14.26 10.098L3.389 17.166 1.564 24h9.008l3.688-13.902Z"

export const integrationLogos: Record<string, IntegrationLogo> = {
	razorpay: {
		background: "#0C2451",
		svg: `${mark(RAZORPAY_GLYPH, "#3395FF", 19, 12, 16)}${lockupWordmark("Razorpay", "#FFFFFF", 39, 13)}`,
	},
	stripe: {
		background: "#635BFF",
		svg: wordmark("stripe", "#FFFFFF", 16),
	},
	telr: {
		background: "#00A9E0",
		svg: wordmark("telr", "#FFFFFF", 16),
	},
	tabby: {
		background: "#12100E",
		svg: `${wordmark("tabby", "#3BFFC3", 16)}${accentBar("#3BFFC3")}`,
	},
	shiprocket: {
		background: "#5B2EDB",
		svg: wordmark("Shiprocket", "#FFFFFF", 13),
	},
	aftership: {
		background: "#0B1B34",
		svg: wordmark("AfterShip", "#FFFFFF", 13),
	},
}

const FALLBACK_BACKGROUND = "#525B66"

function escapeXml(value: string) {
	return value.replace(
		/[&<>"']/g,
		(character) =>
			({
				"&": "&amp;",
				"<": "&lt;",
				">": "&gt;",
				'"': "&quot;",
				"'": "&apos;",
			})[character] as string,
	)
}

/** A provider with no plate of its own still gets the house treatment, keyed off its label. */
function fallbackLogo(label: string): IntegrationLogo {
	const initials = label
		.split(/\s+/)
		.filter(Boolean)
		.slice(0, 2)
		.map((word) => word[0])
		.join("")
		.toUpperCase()
	return {
		background: FALLBACK_BACKGROUND,
		svg: wordmark(escapeXml(initials || "?"), "#FFFFFF", 16),
	}
}

export function getIntegrationLogo(
	slug: string,
	label: string,
): IntegrationLogo {
	return integrationLogos[slug] ?? fallbackLogo(label)
}
