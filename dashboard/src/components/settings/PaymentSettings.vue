<script setup lang="ts">
import {
	Button,
	Checkbox,
	FormControl,
	SettingsBody,
	SettingsHeader,
	SettingsRow,
} from "frappe-ui"
import SettingsLinkField from "./SettingsLinkField.vue"
import { useSettingsForm } from "./useSettingsForm"

const FIELDS = [
	"cod_enabled",
	"cod_charge",
	"cod_charge_applicable_below",
	"charge_account_head",
] as const

const { form, changed, save, submit } = useSettingsForm(
	"payment_settings",
	FIELDS,
	"Payment settings saved",
)
</script>

<template>
	<SettingsHeader
		title="Payments"
		description="Cash on delivery and the account its charge is booked to"
	/>

	<SettingsBody>
		<div class="pt-6">
			<div class="divide-y divide-outline-gray-1">
				<SettingsRow
					title="Cash on delivery"
					description="Let customers pay when the order arrives"
				>
					<Checkbox v-model="form.cod_enabled" />
				</SettingsRow>
				<SettingsRow title="COD charge" description="Extra fee added to a cash-on-delivery order">
					<FormControl v-model="form.cod_charge" type="number" min="0" step="0.01" />
				</SettingsRow>
				<SettingsRow
					title="Charge applicable below"
					description="Orders under this value pay the COD charge"
				>
					<FormControl
						v-model="form.cod_charge_applicable_below"
						type="number"
						min="0"
						step="0.01"
					/>
				</SettingsRow>
				<SettingsRow
					title="Charge account head"
					description="Where the COD charge posts in your accounts"
				>
					<SettingsLinkField v-model="form.charge_account_head" doctype="Account" />
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
