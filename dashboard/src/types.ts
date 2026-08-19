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
