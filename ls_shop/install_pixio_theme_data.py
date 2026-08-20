"""Pixio Theme Settings demo content for the storefront homepage.

Sibling of install_fashion_demo_data.py — that module seeds the catalogue, this one seeds the
homepage copy, banners and picks that read off it, so either can be re-run on its own.

Usage:
    bench --site your-site-name execute ls_shop.install_pixio_theme_data.install_pixio_theme_data
"""

import frappe

from ls_shop.install_fashion_demo_data import IMAGE_ROOT

SETTINGS_DOCTYPE = "Pixio Theme Settings"

PRODUCTS_URL = "/en/products"

HEADLINE_COPY = {
	"hero_caption_label": "Summer Collection",
	"hero_caption": "Trendy and Classic for the New Season",
	"categories_title": "Featured Categories",
	"categories_description": "Discover the most trending products in Pixio.",
	"products_title": "Most popular products",
	"deals_title": "Blockbuster deals",
	"deals_link_label": "See all deals",
	"offers_title": "Featured offer for you",
	"featured_title": "Featured now",
}

HERO_SLIDES = (
	{
		"thumbnail_label": "Winter",
		"heading": "Beautiful Woman Purple Sweater.",
		"subheading": "$80.00",
		"image": "banner/banner-media.png",
	},
	{
		"thumbnail_label": "Summer",
		"heading": "Shot Slad Curly Woman.",
		"subheading": "$30.00",
		"image": "banner/banner-media2.png",
	},
	{
		"thumbnail_label": "Leggings",
		"heading": "Athletic Mesh Sports Leggings.",
		"subheading": "$75.00",
		"image": "banner/banner-media4.png",
	},
	{
		"thumbnail_label": "Dress",
		"heading": "Curly Girl Beautiful Dress.",
		"subheading": "$50.00",
		"image": "banner/banner-media5.png",
	},
)

SHOP_BY_CATEGORY = (
	{"heading": "Shirts", "image": "shop/product/clothes/1.png"},
	{"heading": "Shorts", "image": "shop/product/clothes/2.png"},
	{"heading": "t-Shirt", "image": "shop/product/clothes/3.png"},
	{"heading": "t-Jeans", "image": "shop/product/clothes/4.png"},
	{"heading": "Dresses", "image": "shop/product/clothes/5.png"},
)

COLLECTION_BANNERS = (
	# The first card centres a short heading in .sale-box, the second left-aligns a longer one
	# in .product-content, so the copy is sized to its slot rather than shared between them.
	{"badge_label": "Sale Up to 50% Off", "heading": "Summer Edit", "image": "collection/1.png"},
	{"badge_label": "Sale Up to 50% Off", "heading": "New Summer Collection", "image": "collection/2.png"},
)

OFFER_BANNERS = (
	{"badge_label": "20% Off", "heading": "Luxury Bras", "image": "collection/3.png"},
	{"badge_label": "Sale Up to 50% Off", "heading": "Summer", "image": "collection/4.png"},
	{"badge_label": "20% Off", "heading": "Swimwear", "image": "collection/5.png"},
)

PICKS = {
	"best_picks": (
		"KNIT-CARDIGAN - Pink",
		"SWAGGER-SUIT - Pink",
		"DENIM-SKINNY-JEANS - Blue",
		"MESH-LEGGINGS - Red",
		"DENIM-OVERALL-SHORTS - Blue",
		"PRINTED-SPREAD-SHIRT - Maroon",
	),
	"deal_picks": (
		"CHECKERED-SLIM-SHIRT - Blue",
		"SOLID-CUTAWAY-SHIRT - Gray",
		"CHECKERED-SPREAD-SHIRT - Red",
		"KNIT-CARDIGAN - Purple",
	),
	"featured_picks": (
		"SWAGGER-SUIT - Blush",
		"DENIM-SKINNY-JEANS - Navy",
		"MESH-LEGGINGS - Crimson",
		"PRINTED-SPREAD-SHIRT - Rust",
	),
}

SOCIAL_URLS = {
	"facebook_url": "https://facebook.com/lsshop",
	"twitter_url": "https://twitter.com/lsshop",
	"instagram_url": "https://instagram.com/lsshop",
	"tiktok_url": "https://tiktok.com/@lsshop",
	"snapchat_url": "https://snapchat.com/add/lsshop",
}


def install_pixio_theme_data():
	"""Seed the Pixio homepage copy, banners and picks. Safe to re-run."""
	settings = frappe.get_doc(SETTINGS_DOCTYPE)

	for fieldname, value in HEADLINE_COPY.items():
		if not settings.get(fieldname):
			settings.set(fieldname, value)

	save_child_rows(settings, "hero_slides", banner_rows(HERO_SLIDES, "More Collection Explore"))
	save_child_rows(settings, "shop_by_category", banner_rows(SHOP_BY_CATEGORY))
	save_child_rows(settings, "collection_banners", banner_rows(COLLECTION_BANNERS, "Shop Now"))
	save_child_rows(settings, "offer_banners", banner_rows(OFFER_BANNERS, "Collect Now"))

	for fieldname, variant_names in PICKS.items():
		save_child_rows(settings, fieldname, pick_rows(variant_names))

	settings.save(ignore_permissions=True)
	save_social_urls()

	# nosemgrep: manual commit required, this runs outside a request
	frappe.db.commit()
	frappe.clear_cache()


def save_child_rows(settings, fieldname, rows):
	"""Fill a table only while it is still empty, so a re-run never duplicates and never
	overwrites content the merchant has since curated in Desk."""
	if settings.get(fieldname) or not rows:
		return

	for row in rows:
		settings.append(fieldname, row)


def banner_rows(banners, cta_label=None):
	rows = []
	for banner in banners:
		row = dict(banner, image=f"{IMAGE_ROOT}/{banner['image']}", url=PRODUCTS_URL)
		if cta_label:
			row["cta_label"] = cta_label
		rows.append(row)

	return rows


def pick_rows(variant_names):
	"""A pick whose variant is missing is dropped — the catalogue seeder is optional and a
	dangling link would fail the save instead of just rendering one card less."""
	existing = set(
		frappe.get_all("Style Attribute Variant", filters={"name": ["in", list(variant_names)]}, pluck="name")
	)

	return [{"item_variant": name} for name in variant_names if name in existing]


def save_social_urls():
	"""Demo placeholder handles, not the merchant's real accounts — replace them in Lifestyle
	Settings before going live.

	Written field-wise rather than through the doc because Lifestyle Settings.validate rejects a
	site that has no payment method configured yet, which a freshly seeded site usually has not.
	"""
	settings = frappe.get_cached_doc("Lifestyle Settings")
	for fieldname, url in SOCIAL_URLS.items():
		if not settings.get(fieldname):
			frappe.db.set_single_value("Lifestyle Settings", fieldname, url)
