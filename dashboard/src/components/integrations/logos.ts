/**
 * Brand plates for the integration cards. One house treatment for every provider — a rounded
 * brand-coloured tile with a centred wordmark — so a row of them reads as a set.
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

export const integrationLogos: Record<string, IntegrationLogo> = {
	razorpay: {
		background: "#0C2451",
		svg: `${wordmark("Razorpay", "#FFFFFF", 13)}${accentBar("#3395FF")}`,
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
