import type { ColorScheme, KeyboardShortcutCombo } from "frappe-ui"

/**
 * The app-chrome tables: one list of places the owner can go, and one list of theme choices.
 * The sidebar, the command palette and the keyboard-shortcut registry all read them, so a
 * destination cannot exist in one of the three and be missing from the others.
 */

export type NavDestination = {
	label: string
	/** Route name, as declared in router.ts. */
	route: string
	icon: string
	shortcut?: KeyboardShortcutCombo
	/** Sidebar group heading; the leading run is pinned above the first heading and has none. */
	group?: string
}

export const navDestinations: NavDestination[] = [
	{
		label: "Home",
		route: "Home",
		icon: "lucide-house",
		shortcut: "Mod+Shift+H",
	},
	{
		label: "Orders",
		route: "Orders",
		icon: "lucide-receipt",
		shortcut: "Mod+Shift+O",
	},
	{
		label: "Analytics",
		route: "Analytics",
		icon: "lucide-chart-no-axes-column",
	},
	{
		label: "Products",
		route: "Products",
		icon: "lucide-package",
		shortcut: "Mod+Shift+P",
		group: "Catalog",
	},
	{
		label: "Inventory",
		route: "Inventory",
		icon: "lucide-boxes",
		// Not Mod+Shift+I: that is the browser's own devtools shortcut on every platform, so the
		// keystroke is swallowed before the app ever sees it.
		shortcut: "Mod+Shift+U",
		group: "Catalog",
	},
	{
		label: "Navigation",
		route: "Navigation",
		icon: "lucide-menu",
		shortcut: "Mod+Shift+M",
		group: "Storefront",
	},
	{
		label: "Footer",
		route: "Footer",
		icon: "lucide-panel-bottom",
		shortcut: "Mod+Shift+F",
		group: "Storefront",
	},
]

export type NavSection = {
	/** Empty for the pinned top-level run, which carries no group heading. */
	label: string
	destinations: NavDestination[]
}

/**
 * The destinations cut into the sidebar's runs, in table order. Grouped by the job the owner
 * came to do, not by which doctype backs the page, the way CRM and Gameplan pin their everyday
 * destinations above the first group header.
 */
export const navSections: NavSection[] = navDestinations.reduce<NavSection[]>(
	(sections, destination) => {
		const label = destination.group ?? ""
		const current = sections.at(-1)
		if (current?.label === label) current.destinations.push(destination)
		else sections.push({ label, destinations: [destination] })
		return sections
	},
	[],
)

export type ColorSchemeOption = {
	label: string
	value: ColorScheme
	icon: string
}

export const colorSchemeOptions: ColorSchemeOption[] = [
	{ label: "Light", value: "light", icon: "lucide-sun" },
	{ label: "Dark", value: "dark", icon: "lucide-moon" },
	{ label: "System default", value: "system", icon: "lucide-monitor" },
]
