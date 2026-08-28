import type { BadgeProps, ButtonProps } from "frappe-ui"

/** The one field we read off frappe-ui's FileUploader success payload. */
export type UploadedFile = {
	file_url: string
}

export type ProductSize = {
	size: string
	item_code: string
	rate: number | null
	stock: number
}

export type ProductVariant = {
	name: string
	option: string
	is_published: boolean
	route: string | null
	storefront_url: string | null
	sizes: ProductSize[]
	images: string[]
	blockers: string[]
}

export type ProductDetail = {
	name: string
	title: string
	image: string | null
	collection: string
	description: string | null
	disabled: boolean
	option_attribute: string | null
	variants: ProductVariant[]
}

export type ProductRow = {
	name: string
	title: string
	image: string | null
	collection: string
	disabled: boolean
	variant_count: number
	published_count: number
	price_from: number | null
	price_to: number | null
	stock: number
}

/** Every analytics endpoint reads the same inclusive window from the one page-level range control. */
export type AnalyticsRangeParams = {
	from_date: string
	to_date: string
}

/**
 * What a list screen puts in place of its rows. ListView v-binds `button` straight onto a Button,
 * so the click handler travels with the rest of the button's props.
 */
export type ListEmptyState = {
	title: string
	description: string
	button?: ButtonProps & { onClick: () => void }
}

/** Taken from the Badge component itself, so our map cannot drift from what frappe-ui ships. */
export type BadgeTheme = NonNullable<BadgeProps["theme"]>
export type BadgeVariant = NonNullable<BadgeProps["variant"]>

/** A stable key for the icon and colour, plus the label the store owner reads. */
export type OrderState = {
	key: string
	label: string
}

export type OrderRow = {
	name: string
	customer: string
	placed_on: string
	status: string
	state: OrderState
	total: number
	currency: string
	item_count: number
	payment_mode: string | null
}

export type OrderItem = {
	item_code: string
	title: string
	size: string | null
	qty: number
	delivered_qty: number
	rate: number
	amount: number
	image: string | null
}

export type OrderDetail = {
	name: string
	customer: string
	email: string | null
	phone: string | null
	placed_on: string
	status: string
	state: OrderState
	currency: string
	total: number
	/**
	 * The charges that make up the difference between `net_total` and `grand_total`. `tax` is the
	 * remainder of the charges table rather than a tax figure in its own right, so the four always
	 * sum to the total even when a charge row is of a kind neither side recognises.
	 */
	net_total: number
	shipping: number
	cod_charge: number
	tax: number
	total_taxes_and_charges: number
	grand_total: number
	payment_mode: string | null
	shipping_address: string | null
	can_fulfil: boolean
	items: OrderItem[]
	deliveries: string[]
}

export type InventoryRow = {
	item_code: string
	product: string
	product_name: string
	option: string
	variant: string
	size: string
	stock: number
	is_published: boolean
	availability: string
}

export type MenuLinkType = "" | "Item Group" | "Brand" | "URL"

export type MenuNode = {
	name: string
	label: string
	parent: string
	route_slug: string
	link_type: MenuLinkType
	item_groups: string[]
	brand: string
	url: string
	icon: string
	image: string
	meta_title: string
	meta_description: string
	og_image: string
	noindex: number
	visible: boolean
	display_order: number
	href: string | null
	children: MenuNode[]
	/** Owned by frappe-ui's Tree, which reads and writes open state on the node itself. */
	expanded?: boolean
}

export type CascadeProduct = {
	name: string
	display_name: string
	item_group: string
	is_published: number
	blocked_reason: string
}

export type OverviewStat = {
	key: string
	label: string
	value: number
	format: "currency" | "number"
	delta: number | null
	note?: string
}

export type BlockedOption = {
	variant: string
	product: string
	title: string
	option: string
	blockers: string[]
}

export type Overview = {
	currency: string
	window_days: number
	stats: OverviewStat[]
	recent_orders: OrderRow[]
	running_low: InventoryRow[]
	needs_attention: BlockedOption[]
}

export type FooterLink = {
	name: string
	parent: string
	link_label: string
	link_url: string
	link_order: number
	enabled: number
}

export type FooterSection = {
	name: string
	title: string
	section_order: number
	enabled: number
	links: FooterLink[]
}

export type FooterPage = {
	name: string
	route: string
}

export type FooterEditorData = {
	columns: FooterSection[]
	pages: FooterPage[]
	modified: string
}

// ── Storefront analytics ────────────────────────────────────────────────────
// One type per `ls_shop.api.analytics_dashboard` endpoint, named after it.

/** Every KPI tile carries the same figure for the equal-length window before it. */
export type AnalyticsKpi = {
	value: number
	previous: number
}

export type AnalyticsKpiKey =
	| "total_sales"
	| "orders"
	| "sessions"
	| "conversion_rate"
	| "aov"
	| "returning_customer_rate"

export type AnalyticsOverview = {
	currency: string
	kpis: Record<AnalyticsKpiKey, AnalyticsKpi>
}

export type SalesTimeseries = {
	labels: string[]
	sales: number[]
	orders: number[]
}

export type FunnelStageRow = {
	key: string
	label: string
	count: number
}

export type FunnelReport = {
	stages: FunnelStageRow[]
}

export type LiveView = {
	visitors_now: number
	today: { sessions: number; orders: number; sales: number }
	active_carts: number
	checking_out: number
}

export type TopProduct = {
	item_code: string
	item_name: string
	units: number
	revenue: number
}

export type ProductEngagementRow = {
	item_code: string
	item_name: string
	views: number
	adds: number
	purchases: number
	cart_to_view_rate: number
	purchase_to_view_rate: number
}

export type TrafficSourceRow = {
	source: string
	medium: string
	/** Empty for direct and organic traffic, which legitimately runs no campaign. */
	campaign: string
	sessions: number
	orders: number
	revenue: number
	conversion_rate: number
}

export type DeviceSplitRow = {
	device: string
	sessions: number
	conversion_rate: number
}

export type LandingPageRow = {
	path: string
	sessions: number
	conversion_rate: number
}

export type AbandonedCartStatus = "Abandoned" | "Recoverable" | "Recovered"

export type AbandonedCartRow = {
	session_id: string
	customer: string | null
	email: string | null
	items_count: number
	value: number
	last_activity: string
	status: AbandonedCartStatus
	quotation: string | null
}

export type AbandonedCarts = {
	stats: { count: number; value: number; rate: number }
	carts: AbandonedCartRow[]
}

/** `matrix[weekday][hour]`, weekday 0 = Monday. */
export type SalesHeatmap = {
	matrix: number[][]
	max: number
}

export type ProviderHealth = {
	configured: boolean
	ok: boolean
	purchases_30d: number | null
	error: string | null
}

export type TrackingHealth = {
	first_party: { events_24h: number; purchases_30d: number }
	ga4: ProviderHealth
	meta: ProviderHealth
}

/** GA4 keys its daily series `daily_sessions`, Meta keys its own `daily_pageviews`. */
export type ProviderSummary = {
	totals: Record<string, number>
	daily_sessions?: Record<string, number>
	daily_pageviews?: Record<string, number>
}

export type ProviderReadback = {
	configured: boolean
	summary: ProviderSummary | null
	error: string | null
}

export type ExternalSummaries = {
	ga4: ProviderReadback
	meta: ProviderReadback
}

export type ItemAnalytics = {
	item_code: string
	item_name: string
	totals: {
		views: number
		adds: number
		checkouts: number
		units_sold: number
		revenue: number
		cart_to_view_rate: number
		purchase_to_view_rate: number
		store_avg_purchase_to_view_rate: number
	}
	daily: { labels: string[]; views: number[]; adds: number[]; units: number[] }
	devices: { device: string; views: number }[]
	sources: { source: string; medium: string; views: number; adds: number }[]
	recent_orders: { order: string; date: string; qty: number; amount: number }[]
}
