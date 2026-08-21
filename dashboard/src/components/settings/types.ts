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
	enabled: number
	script: string
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
