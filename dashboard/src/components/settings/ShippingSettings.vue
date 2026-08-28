<script setup lang="ts">
import {
	FormControl,
	SettingsBody,
	SettingsHeader,
	SettingsRow,
} from "frappe-ui"
import { computed } from "vue"
import IntegrationList from "../integrations/IntegrationList.vue"
import SettingsLinkField from "./SettingsLinkField.vue"
import SettingsSaveButton from "./SettingsSaveButton.vue"
import type { ShippingSettingsData } from "./types"
import { useSettingsForm } from "./useSettingsForm"

const FIELDS = ["shipping_rule", "return_period"] as const

const { settings, form, text, changed, save, submit } = useSettingsForm<
	(typeof FIELDS)[number],
	ShippingSettingsData
>("shipping_settings", FIELDS, "Shipping and returns saved")

const returnReasons = computed(() => settings.data?.reason_for_return ?? [])
</script>

<template>
	<SettingsHeader
		title="Shipping & returns"
		description="The carriers that deliver your orders, and how long customers have to send them back"
	/>

	<SettingsBody>
		<div class="pt-6">
			<h3 class="text-base font-medium text-ink-gray-8">Delivery partners</h3>
			<p class="mt-1 text-p-sm text-ink-gray-5">
				Turn on a carrier and add its credentials to quote live rates and book shipments.
			</p>
			<IntegrationList
				class="mt-2"
				list-url="/api/v2/method/ls_shop.api.admin.shipping.get_shipping_integrations"
				save-url="/api/v2/method/ls_shop.api.admin.shipping.save_shipping_integration"
			/>

			<h3 class="mt-8 text-base font-medium text-ink-gray-8">Rates &amp; returns</h3>
			<div class="mt-2 divide-y divide-outline-gray-1">
				<SettingsRow
					title="Shipping rule"
					description="Decides the delivery charge applied at checkout"
				>
					<SettingsLinkField v-model="text.shipping_rule" doctype="Shipping Rule" />
				</SettingsRow>
				<SettingsRow
					title="Return period"
					description="Days after the invoice a customer can still return an item"
				>
					<FormControl v-model="form.return_period" type="number" min="0" />
				</SettingsRow>
			</div>

			<SettingsSaveButton :loading="save.loading" :disabled="!changed" @save="submit()" />

			<div class="mt-8">
				<h3 class="text-base font-medium text-ink-gray-8">Return reasons</h3>
				<p class="mt-1 text-p-sm text-ink-gray-5">
					The reasons a customer can pick when returning an item. Managed in Desk.
				</p>
				<ul
					v-if="returnReasons.length"
					class="mt-3 divide-y divide-outline-gray-1 border-y border-outline-gray-1"
				>
					<li v-for="reason in returnReasons" :key="reason.name" class="py-2.5">
						<div class="text-base text-ink-gray-8">{{ reason.display_name }}</div>
						<p v-if="reason.description" class="mt-0.5 text-p-sm text-ink-gray-5">
							{{ reason.description }}
						</p>
					</li>
				</ul>
				<p v-else class="mt-3 text-p-sm text-ink-gray-5">No return reasons set up yet.</p>
			</div>
		</div>
	</SettingsBody>
</template>
