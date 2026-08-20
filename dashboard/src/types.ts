import type { BadgeProps } from "frappe-ui"

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
