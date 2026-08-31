import { computed, unref } from 'vue'
import { collections, inventory, locations, orders, productTypes } from './mock'

// Everything the product screen needs to summarise a product at a glance,
// derived from the same mock records the list screens read.
export function useProductStats(source) {
  return computed(() => {
    const product = unref(source)
    const units = product.hasVariants ? product.variants : [{ ...product, title: '—' }]
    const prices = units.map((u) => u.price)
    const rows = inventory.filter((row) => row.productId === product.id)

    const onHand = rows.reduce((sum, row) => sum + row.onHand, 0)
    const committed = rows.reduce((sum, row) => sum + row.committed, 0)

    const lines = orders.flatMap((order) =>
      order.items
        .filter((item) => item.productId === product.id)
        .map((item) => ({ ...item, order })),
    )

    return {
      priceLow: Math.min(...prices),
      priceHigh: Math.max(...prices),
      variantCount: product.variants.length,
      optionCount: product.options.length,
      onHand,
      committed,
      available: onHand - committed,
      outOfStock: units.filter((u) => (u.stock ?? 0) <= 0).length,
      lowStock: units.filter((u) => (u.stock ?? 0) > 0 && (u.stock ?? 0) <= 5).length,
      byLocation: locations.map((location) => ({
        ...location,
        onHand: rows.filter((row) => row.locationId === location.id).reduce((s, r) => s + r.onHand, 0),
      })),
      unitsSold: lines.reduce((sum, line) => sum + line.qty, 0),
      revenue: lines.reduce((sum, line) => sum + line.qty * line.price, 0),
      orderCount: new Set(lines.map((line) => line.order.id)).size,
      recentOrders: lines.slice(0, 3).map((line) => line.order),
      type: productTypes.find((t) => t.id === product.type),
      collections: collections.filter((c) => product.collections.includes(c.id)),
      // Top sellers first — the rows a merchant actually watches.
      topVariants: [...units].sort((a, b) => (b.stock ?? 0) - (a.stock ?? 0)).slice(0, 4),
      lowVariants: units.filter((u) => (u.stock ?? 0) <= 5).slice(0, 4),
    }
  })
}
