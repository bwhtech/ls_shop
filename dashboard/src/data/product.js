import { computed, unref } from 'vue'

// Everything the product screen needs to summarise a product at a glance,
// derived from catalog.get_product's real shape: a product's sellable units
// are its variants' *sizes* (Color Size Item rows), not the variants
// themselves — a variant (Style Attribute Variant) is one option like a
// colour, and each of its sizes carries its own price and stock.
export function useProductStats(source) {
  return computed(() => {
    const product = unref(source)
    const sizes = product.variants.flatMap((variant) =>
      variant.sizes.map((size) => ({ ...size, variant })),
    )

    const onHand = sizes.reduce((sum, size) => sum + (size.stock ?? 0), 0)
    const committed = sizes.reduce((sum, size) => sum + (size.committed ?? 0), 0)
    const rates = sizes.map((size) => size.default_rate).filter((rate) => rate != null)

    const sales = product.recent_sales ?? { units_sold: 0, order_count: 0, revenue: 0 }

    return {
      priceLow: rates.length ? Math.min(...rates) : null,
      priceHigh: rates.length ? Math.max(...rates) : null,
      variantCount: product.variants.length,
      sizeCount: sizes.length,
      onHand,
      committed,
      available: onHand - committed,
      outOfStock: sizes.filter((size) => (size.stock ?? 0) <= 0).length,
      lowStock: sizes.filter((size) => (size.stock ?? 0) > 0 && (size.stock ?? 0) <= 5).length,
      unitsSold: sales.units_sold,
      revenue: sales.revenue,
      orderCount: sales.order_count,
      // Lowest-stock sizes first — the rows a merchant actually needs to act on.
      lowVariants: sizes
        .filter((size) => (size.stock ?? 0) <= 5)
        .sort((a, b) => (a.stock ?? 0) - (b.stock ?? 0))
        .slice(0, 4)
        .map((size) => ({
          id: size.item_code,
          title: `${size.variant.option} · ${size.size}`,
          image: size.variant.images?.[0],
          stock: size.stock,
        })),
    }
  })
}
