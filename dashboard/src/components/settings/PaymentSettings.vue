<script setup lang="ts">
import {
	Button,
	Checkbox,
	FormControl,
	SettingsBody,
	SettingsHeader,
	SettingsRow,
} from "frappe-ui"
import IntegrationList from "../integrations/IntegrationList.vue"
import SettingsLinkField from "./SettingsLinkField.vue"
import { useSettingsForm } from "./useSettingsForm"

const FIELDS = [
	"cod_enabled",
	"cod_charge",
	"cod_charge_applicable_below",
	"charge_account_head",
] as const

const { form, text, checked, changed, save, submit } = useSettingsForm(
	"payment_settings",
	FIELDS,
	"Payment settings saved",
)
</script>

<template>
	<SettingsHeader
		title="Payments"
		description="The gateways customers can pay with, and how cash on delivery is charged"
	/>

	<SettingsBody>
		<div class="pt-6">
			<h3 class="text-base font-medium text-ink-gray-8">Payment gateways</h3>
			<p class="mt-1 text-p-sm text-ink-gray-5">
				Turn on a provider and add its credentials to take online payments.
			</p>
			<IntegrationList
				class="mt-2"
				list-url="/api/v2/method/ls_shop.api.admin.payments.get_payment_integrations"
				save-url="/api/v2/method/ls_shop.api.admin.payments.save_payment_integration"
			/>

			<h3 class="mt-8 text-base font-medium text-ink-gray-8">Cash on delivery</h3>
			<div class="mt-2 divide-y divide-outline-gray-1">
				<SettingsRow
					title="Accept cash on delivery"
					description="Let customers pay when the order arrives"
				>
					<Checkbox v-model="checked.cod_enabled" />
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
					<SettingsLinkField v-model="text.charge_account_head" doctype="Account" />
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
