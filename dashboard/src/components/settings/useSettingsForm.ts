import { toast, useCall } from "frappe-ui"
import { computed, reactive, toRaw, watch } from "vue"

const METHOD_PREFIX = "/api/v2/method/ls_shop.api.admin.settings."

export type SettingsValue = string | number | boolean | null

/** Frappe stores checks as 1/0 and numbers as numbers, while inputs hand back strings. */
export function normalizeValue(value: unknown): string {
	if (value === true) return "1"
	if (value === false) return "0"
	if (value === null || value === undefined) return ""
	return String(value)
}

/**
 * One load/edit/save cycle for a slice of Lifestyle Settings, shared by every settings tab
 * so each tab is only its field list and its markup.
 */
export function useSettingsForm(
	resource: string,
	fieldnames: readonly string[],
	savedMessage: string,
) {
	const settings = useCall<Record<string, SettingsValue>>({
		url: `${METHOD_PREFIX}get_${resource}`,
	})

	const form = reactive<Record<string, SettingsValue>>(
		Object.fromEntries(fieldnames.map((fieldname) => [fieldname, null])),
	)

	watch(
		() => settings.data,
		(data) => {
			if (!data) return
			for (const fieldname of fieldnames)
				form[fieldname] = data[fieldname] ?? null
		},
		{ immediate: true },
	)

	const changed = computed(() => {
		const data = settings.data
		if (!data) return false
		return fieldnames.some(
			(fieldname) =>
				normalizeValue(form[fieldname]) !== normalizeValue(data[fieldname]),
		)
	})

	const save = useCall<Record<string, SettingsValue>>({
		url: `${METHOD_PREFIX}save_${resource}`,
		method: "POST",
		immediate: false,
		onSuccess: () => {
			toast.success(savedMessage)
			settings.reload()
		},
		onError: (error: Error) => toast.error(error.message),
	})

	function submit(overrides: Record<string, SettingsValue> = {}) {
		save.submit({ ...toRaw(form), ...overrides })
	}

	return { settings, form, changed, save, submit }
}
