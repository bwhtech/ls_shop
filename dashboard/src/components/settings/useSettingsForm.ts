import { errorMessage } from "@/utils/errors"
import { toast, useCall } from "frappe-ui"
import type { WritableComputedRef } from "vue"
import { computed, reactive, toRaw, watch } from "vue"

const METHOD_PREFIX = "/api/v2/method/ls_shop.api.admin."

export type SettingsValue = string | number | boolean | null

/** Frappe stores checks as 1/0 and numbers as numbers, while inputs hand back strings. */
export function normalizeValue(value: unknown): string {
	if (value === true) return "1"
	if (value === false) return "0"
	if (value === null || value === undefined) return ""
	return String(value)
}

export function useSettingsForm<
	TFieldname extends string,
	TSettings extends Record<TFieldname, SettingsValue> = Record<
		TFieldname,
		SettingsValue
	>,
>(
	resource: string,
	fieldnames: readonly TFieldname[],
	savedMessage: string,
	apiModule = "settings",
) {
	const settings = useCall<TSettings>({
		url: `${METHOD_PREFIX}${apiModule}.get_${resource}`,
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

	/**
	 * `Object.fromEntries` types its keys as a plain string index, which is why the map is named
	 * before `reactive` unwraps each ref into a plain property.
	 */
	const textRefs = Object.fromEntries(
		fieldnames.map((fieldname) => [
			fieldname,
			computed({
				get: () =>
					form[fieldname] === null ? null : normalizeValue(form[fieldname]),
				set: (value: string | null) => {
					form[fieldname] = value
				},
			}),
		]),
	) as Record<TFieldname, WritableComputedRef<string | null>>

	const checkRefs = Object.fromEntries(
		fieldnames.map((fieldname) => [
			fieldname,
			computed({
				get: () => normalizeValue(form[fieldname]) === "1",
				set: (value: boolean) => {
					form[fieldname] = value
				},
			}),
		]),
	) as Record<TFieldname, WritableComputedRef<boolean>>

	const text = reactive(textRefs)
	const checked = reactive(checkRefs)

	const changed = computed(() => {
		const data = settings.data
		if (!data) return false
		return fieldnames.some(
			(fieldname) =>
				normalizeValue(form[fieldname]) !== normalizeValue(data[fieldname]),
		)
	})

	const save = useCall<TSettings, Record<string, SettingsValue>>({
		url: `${METHOD_PREFIX}${apiModule}.save_${resource}`,
		method: "POST",
		immediate: false,
		onSuccess: () => {
			toast.success(savedMessage)
			settings.reload()
		},
		onError: (error: Error) => toast.error(errorMessage(error)),
	})

	function submit(overrides: Record<string, SettingsValue> = {}) {
		save.submit({ ...toRaw(form), ...overrides })
	}

	return { settings, form, text, checked, changed, save, submit }
}
