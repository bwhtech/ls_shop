<script setup lang="ts">
import {
	Button,
	FormControl,
	SettingsBody,
	SettingsHeader,
	SettingsRow,
} from "frappe-ui"
import { computed } from "vue"
import SettingsLinkField from "./SettingsLinkField.vue"
import { useSettingsForm } from "./useSettingsForm"

type ReturnReason = {
	name: string
	display_name: string
	description: string | null
}

const FIELDS = ["shipping_rule", "return_period"] as const

const { settings, form, changed, save, submit } = useSettingsForm(
	"shipping_settings",
	FIELDS,
	"Shipping and returns saved",
)

const returnReasons = computed(
	() => (settings.data?.reason_for_return ?? []) as unknown as ReturnReason[],
)
</script>

<template>
	<SettingsHeader
		title="Shipping & returns"
		description="How orders reach customers and how long they have to send them back"
	/>

	<SettingsBody>
		<div class="pt-6">
			<div class="divide-y divide-outline-gray-1">
				<SettingsRow
					title="Shipping rule"
					description="Decides the delivery charge applied at checkout"
				>
					<SettingsLinkField v-model="form.shipping_rule" doctype="Shipping Rule" />
				</SettingsRow>
				<SettingsRow
					title="Return period"
					description="Days after the invoice a customer can still return an item"
				>
					<FormControl v-model="form.return_period" type="number" min="0" />
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
