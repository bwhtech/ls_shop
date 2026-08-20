<script setup lang="ts">
import {
	Button,
	FormControl,
	SettingsBody,
	SettingsHeader,
	SettingsRow,
} from "frappe-ui"
import SettingsAttach from "./SettingsAttach.vue"
import SettingsLinkField from "./SettingsLinkField.vue"
import { useSettingsForm } from "./useSettingsForm"

const FIELDS = [
	"store_name",
	"brand_logo",
	"footer_logo",
	"favicon",
	"contact_email",
	"contact_phone",
	"working_hours",
	"company",
] as const

const { form, changed, save, submit } = useSettingsForm(
	"store_settings",
	FIELDS,
	"Store details saved",
)
</script>

<template>
	<SettingsHeader
		title="Store details"
		description="How your storefront names itself and how customers reach you"
	/>

	<SettingsBody>
		<div class="pt-6">
			<div class="divide-y divide-outline-gray-1">
				<SettingsRow title="Store name" description="Shown across your storefront">
					<FormControl v-model="form.store_name" />
				</SettingsRow>
				<SettingsRow title="Brand logo" description="Used in the storefront header">
					<SettingsAttach v-model="form.brand_logo" />
				</SettingsRow>
				<SettingsRow title="Footer logo">
					<SettingsAttach v-model="form.footer_logo" />
				</SettingsRow>
				<SettingsRow title="Favicon" description="The small icon in the browser tab">
					<SettingsAttach v-model="form.favicon" :image="false" />
				</SettingsRow>
				<SettingsRow title="Contact email" description="Where customers reach you">
					<FormControl v-model="form.contact_email" type="email" />
				</SettingsRow>
				<SettingsRow title="Contact phone">
					<FormControl v-model="form.contact_phone" />
				</SettingsRow>
				<SettingsRow title="Working hours" description="Shown alongside your contact details">
					<FormControl v-model="form.working_hours" />
				</SettingsRow>
				<SettingsRow title="Company" description="The ERPNext company orders are booked against">
					<SettingsLinkField v-model="form.company" doctype="Company" />
				</SettingsRow>
			</div>

			<div class="flex justify-end pt-4">
				<Button
					variant="solid"
					theme="gray"
					:loading="save.loading"
					:disabled="!changed"
					label="Save"
					@click="submit()"
				/>
			</div>
		</div>
	</SettingsBody>
</template>
