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

export type OrderRow = {
	name: string
	customer: string
	placed_on: string
	status: string
	state: string
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
	state: string
	currency: string
	total: number
	grand_total: number
	payment_mode: string | null
	shipping_address: string | null
	can_fulfil: boolean
	items: OrderItem[]
	deliveries: string[]
}
