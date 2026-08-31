import { createRouter, createWebHistory } from "vue-router"

// Detail pages are nested under their list route — with no component on the parent
// the child renders alone, but `route.matched` still carries the section record so
// the sidebar can keep that section highlighted while you are drilled into a detail.
const routes = [
	{ path: "/", redirect: "/store/home" },
	{
		path: "/store/home",
		name: "Home",
		component: () => import("@/pages/Home.vue"),
	},
	{
		path: "/store/products",
		children: [
			{
				path: "",
				name: "Products",
				component: () => import("@/pages/Products.vue"),
			},
			{
				path: ":name",
				name: "Product",
				component: () => import("@/pages/Product.vue"),
			},
		],
	},
	{
		path: "/store/inventory",
		name: "Inventory",
		component: () => import("@/pages/Inventory.vue"),
	},
	{
		path: "/store/orders",
		children: [
			{
				path: "",
				name: "Orders",
				component: () => import("@/pages/Orders.vue"),
			},
			{
				path: ":name",
				name: "Order",
				component: () => import("@/pages/Order.vue"),
			},
		],
	},
	{
		path: "/store/analytics",
		children: [
			{ path: "", redirect: { name: "SalesAnalytics" } },
			{
				path: "sales",
				name: "SalesAnalytics",
				component: () => import("@/pages/analytics/Sales.vue"),
			},
			{
				path: "website",
				name: "WebsiteAnalytics",
				component: () => import("@/pages/analytics/Website.vue"),
			},
		],
	},
	{
		path: "/storefront/navigation",
		name: "Navigation",
		component: () => import("@/pages/Navigation.vue"),
	},
	{
		path: "/storefront/footer",
		name: "Footer",
		component: () => import("@/pages/Footer.vue"),
	},
]

export default createRouter({
	history: createWebHistory("/dashboard"),
	routes,
})
