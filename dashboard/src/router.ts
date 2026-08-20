import { createRouter, createWebHistory } from "vue-router"

// Routes are grouped by top-level area (/store, /storefront, ...) so the shell can grow a
// Rail later without reorganising the app.
const routes = [
	{ path: "/", redirect: "/store/products" },
	{
		path: "/store/products",
		name: "Products",
		component: () => import("@/pages/Products.vue"),
	},
	{
		path: "/store/products/:name",
		name: "Product",
		component: () => import("@/pages/Product.vue"),
	},
	{
		path: "/store/inventory",
		name: "Inventory",
		component: () => import("@/pages/Inventory.vue"),
	},
	{
		path: "/store/orders",
		name: "Orders",
		component: () => import("@/pages/Orders.vue"),
	},
	{
		path: "/store/orders/:name",
		name: "Order",
		component: () => import("@/pages/Order.vue"),
	},
	{
		path: "/storefront/navigation",
		name: "Navigation",
		component: () => import("@/pages/Navigation.vue"),
	},
]

export default createRouter({
	history: createWebHistory("/dashboard"),
	routes,
})
