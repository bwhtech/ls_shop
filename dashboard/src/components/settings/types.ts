/** A single editable Lifestyle Settings field as the generic Advanced tab receives it. */
export type AdvancedField = {
	fieldname: string
	label: string
	fieldtype: string
	options: string | null
	description: string | null
}

/** One row of the Analytics Settings custom tracking script table. */
export type CustomTrackingScript = {
	title: string
	enabled: 0 | 1
	script: string
}

/** One row of the Reason for Return table that rides along with the shipping settings. */
export type ReturnReason = {
	name: string
	display_name: string
	description: string | null
}

/** What ls_shop.api.admin.settings.get_shipping_settings returns. */
export type ShippingSettingsData = {
	shipping_rule: string | null
	return_period: number | null
	reason_for_return: ReturnReason[]
}

/** What ls_shop.api.admin.analytics.get_analytics_settings returns - never a secret value. */
export type AnalyticsSettingsData = {
	enable_first_party: number
	enable_ga4: number
	ga4_measurement_id: string | null
	ga4_property_id: string | null
	ga4_service_account_json_is_set: boolean
	enable_facebook: number
	fb_pixel_id: string | null
	fb_access_token_is_set: boolean
	ga4_configured: boolean
	meta_configured: boolean
	custom_tracking_scripts: CustomTrackingScript[]
}
