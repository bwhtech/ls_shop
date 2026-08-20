<script setup lang="ts">
import {
	Button,
	FormControl,
	SettingsBody,
	SettingsHeader,
	SettingsRow,
} from "frappe-ui"
import SettingsAttach from "./SettingsAttach.vue"
import { useSettingsForm } from "./useSettingsForm"

const FIELDS = [
	"facebook_url",
	"twitter_url",
	"instagram_url",
	"snapchat_url",
	"tiktok_url",
	"newsletter_title",
	"newsletter_description",
	"copyright_text",
	"payment_methods_image",
	"vat_certificate_image",
] as const

const SOCIAL_LINKS = [
	{ fieldname: "facebook_url", title: "Facebook" },
	{ fieldname: "twitter_url", title: "Twitter / X" },
	{ fieldname: "instagram_url", title: "Instagram" },
	{ fieldname: "snapchat_url", title: "Snapchat" },
	{ fieldname: "tiktok_url", title: "TikTok" },
]

const { form, changed, save, submit } = useSettingsForm(
	"footer_settings",
	FIELDS,
	"Footer and social saved",
)
</script>

<template>
	<SettingsHeader
		title="Footer & social"
		description="The links, newsletter copy, and badges at the bottom of your storefront"
	/>

	<SettingsBody>
		<div class="space-y-8 pt-6">
			<section>
				<h3 class="text-base font-medium text-ink-gray-8">Social profiles</h3>
				<div class="mt-1 divide-y divide-outline-gray-1">
					<SettingsRow v-for="link in SOCIAL_LINKS" :key="link.fieldname" :title="link.title">
						<FormControl v-model="form[link.fieldname]" type="url" placeholder="https://" />
					</SettingsRow>
				</div>
			</section>

			<section>
				<h3 class="text-base font-medium text-ink-gray-8">Newsletter</h3>
				<div class="mt-1 divide-y divide-outline-gray-1">
					<SettingsRow title="Title">
						<FormControl v-model="form.newsletter_title" />
					</SettingsRow>
					<SettingsRow title="Description">
						<FormControl v-model="form.newsletter_description" type="textarea" :rows="3" class="w-72" />
					</SettingsRow>
				</div>
			</section>

			<section>
				<h3 class="text-base font-medium text-ink-gray-8">Footer content</h3>
				<div class="mt-1 divide-y divide-outline-gray-1">
					<SettingsRow title="Copyright text" description="Shown on the last line of the footer">
						<FormControl v-model="form.copyright_text" />
					</SettingsRow>
					<SettingsRow title="Payment methods image" description="Card and wallet logos">
						<SettingsAttach v-model="form.payment_methods_image" />
					</SettingsRow>
					<SettingsRow title="VAT certificate image">
						<SettingsAttach v-model="form.vat_certificate_image" />
					</SettingsRow>
				</div>
			</section>

			<div class="flex justify-end">
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
