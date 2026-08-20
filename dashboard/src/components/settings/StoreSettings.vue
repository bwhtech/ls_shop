<script setup lang="ts">
import {
	Button,
	FormControl,
	SettingsBody,
	SettingsHeader,
	SettingsRow,
	toast,
	useCall,
} from "frappe-ui"
import { computed, reactive, watch } from "vue"

const settings = useCall<Record<string, string>>({
	url: "/api/v2/method/ls_shop.api.admin.settings.get_store_settings",
})

const form = reactive({ store_name: "", contact_email: "", contact_phone: "" })

watch(
	() => settings.data,
	(data) => {
		if (!data) return
		form.store_name = data.store_name ?? ""
		form.contact_email = data.contact_email ?? ""
		form.contact_phone = data.contact_phone ?? ""
	},
	{ immediate: true },
)

const changed = computed(
	() =>
		!!settings.data &&
		(form.store_name !== (settings.data.store_name ?? "") ||
			form.contact_email !== (settings.data.contact_email ?? "") ||
			form.contact_phone !== (settings.data.contact_phone ?? "")),
)

const save = useCall({
	url: "/api/v2/method/ls_shop.api.admin.settings.save_store_settings",
	method: "POST",
	immediate: false,
	onSuccess: () => {
		toast.success("Store details saved")
		settings.reload()
	},
	onError: (error: Error) => toast.error(error.message),
})
</script>

<template>
	<SettingsHeader>
		<h2 class="text-lg font-semibold text-ink-gray-8">Store details</h2>
	</SettingsHeader>

	<SettingsBody>
		<div class="space-y-4 pt-6">
			<SettingsRow title="Store name" description="Shown across your storefront">
				<FormControl v-model="form.store_name" />
			</SettingsRow>
			<SettingsRow title="Contact email" description="Where customers reach you">
				<FormControl v-model="form.contact_email" type="email" />
			</SettingsRow>
			<SettingsRow title="Contact phone">
				<FormControl v-model="form.contact_phone" />
			</SettingsRow>

			<div class="flex justify-end pt-2">
				<Button
					variant="solid"
					theme="gray"
					:loading="save.loading"
					:disabled="!changed"
					label="Save"
					@click="save.submit({ ...form })"
				/>
			</div>
		</div>
	</SettingsBody>
</template>
