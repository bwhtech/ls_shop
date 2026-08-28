<script setup lang="ts">
import {
	Alert,
	Badge,
	Button,
	Checkbox,
	FormControl,
	SettingsBody,
	SettingsHeader,
	SettingsRow,
} from "frappe-ui"
import { computed, reactive, watch } from "vue"
import SettingsSaveButton from "./SettingsSaveButton.vue"
import SettingsSecretField from "./SettingsSecretField.vue"
import type { AnalyticsSettingsData, CustomTrackingScript } from "./types"
import { useSettingsForm } from "./useSettingsForm"

const FIELDS = [
	"enable_first_party",
	"enable_ga4",
	"ga4_measurement_id",
	"ga4_property_id",
	"enable_facebook",
	"fb_pixel_id",
] as const

const SECRET_FIELDS = ["ga4_service_account_json", "fb_access_token"] as const
type SecretFieldname = (typeof SECRET_FIELDS)[number]

const { settings, form, checked, changed, save, submit } = useSettingsForm<
	(typeof FIELDS)[number],
	AnalyticsSettingsData
>("analytics_settings", FIELDS, "Analytics settings saved", "analytics")

const data = computed(() => settings.data)

/** Typed by the owner and sent once; blank means "keep whatever is already stored". */
const secretInputs = reactive<Record<SecretFieldname, string>>({
	ga4_service_account_json: "",
	fb_access_token: "",
})
const clearedSecrets = reactive<Record<SecretFieldname, boolean>>({
	ga4_service_account_json: false,
	fb_access_token: false,
})

const scripts = reactive<{ rows: CustomTrackingScript[] }>({ rows: [] })
const loadedScripts = computed(() =>
	JSON.stringify(data.value?.custom_tracking_scripts ?? []),
)

watch(
	() => settings.data,
	() => {
		for (const fieldname of SECRET_FIELDS) {
			secretInputs[fieldname] = ""
			clearedSecrets[fieldname] = false
		}
		scripts.rows = (data.value?.custom_tracking_scripts ?? []).map((row) => ({
			...row,
		}))
	},
	{ immediate: true },
)

const secretsChanged = computed(() =>
	SECRET_FIELDS.some(
		(fieldname) =>
			secretInputs[fieldname].trim() !== "" || clearedSecrets[fieldname],
	),
)

const scriptsChanged = computed(
	() => JSON.stringify(scripts.rows) !== loadedScripts.value,
)

const anythingChanged = computed(
	() => changed.value || secretsChanged.value || scriptsChanged.value,
)

const ga4Connected = computed(() => Boolean(data.value?.ga4_configured))
const metaConnected = computed(() => Boolean(data.value?.meta_configured))

function addScript() {
	scripts.rows.push({ title: "", enabled: 1, script: "" })
}

function removeScript(index: number) {
	scripts.rows.splice(index, 1)
}

async function saveAnalyticsSettings() {
	await submit({
		...secretInputs,
		cleared_secrets: JSON.stringify(
			SECRET_FIELDS.filter((fieldname) => clearedSecrets[fieldname]),
		),
		custom_tracking_scripts: JSON.stringify(scripts.rows),
	})
}
</script>

<template>
	<SettingsHeader
		title="Analytics & tracking"
		description="Where your storefront's traffic and purchase events are recorded"
	/>

	<SettingsBody>
		<div class="space-y-8 pt-6">
			<section>
				<h3 class="text-base font-medium text-ink-gray-8">First-party event log</h3>
				<div class="mt-1 divide-y divide-outline-gray-1">
					<SettingsRow
						title="Record events in your own database"
						description="Page views, product views, add to cart, checkout and purchase. This is what fills the Storefront Analytics page - no external service involved."
					>
						<Checkbox v-model="checked.enable_first_party" />
					</SettingsRow>
				</div>
			</section>

			<section>
				<div class="flex items-center gap-2">
					<h3 class="text-base font-medium text-ink-gray-8">Google Analytics 4</h3>
					<Badge
						:theme="ga4Connected ? 'green' : 'gray'"
						variant="subtle"
						:label="ga4Connected ? 'Connected' : 'Not connected'"
					/>
				</div>
				<div class="mt-1 divide-y divide-outline-gray-1">
					<SettingsRow
						title="Send events to GA4"
						description="Also reads Sessions and Active Users back onto your analytics page."
					>
						<Checkbox v-model="checked.enable_ga4" />
					</SettingsRow>
					<template v-if="checked.enable_ga4">
						<SettingsRow
							title="Measurement ID"
							description="Your web stream ID, G-XXXXXXXXXX (Admin → Data Streams)"
						>
							<FormControl v-model="form.ga4_measurement_id" placeholder="G-XXXXXXXXXX" />
						</SettingsRow>
						<SettingsRow
							title="Property ID"
							description="The numeric ID under Admin → Property Settings"
						>
							<FormControl v-model="form.ga4_property_id" />
						</SettingsRow>
						<SettingsRow
							title="Service account JSON"
							description="The key file for a service account with Viewer access to the property. Stored encrypted and never shown again."
						>
							<SettingsSecretField
								v-model="secretInputs.ga4_service_account_json"
								v-model:cleared="clearedSecrets.ga4_service_account_json"
								:is-set="Boolean(data?.ga4_service_account_json_is_set)"
								multiline
								placeholder="Paste the whole JSON key file"
							/>
						</SettingsRow>
					</template>
				</div>
			</section>

			<section>
				<div class="flex items-center gap-2">
					<h3 class="text-base font-medium text-ink-gray-8">Meta Pixel</h3>
					<Badge
						:theme="metaConnected ? 'green' : 'gray'"
						variant="subtle"
						:label="metaConnected ? 'Connected' : 'Not connected'"
					/>
				</div>
				<div class="mt-1 divide-y divide-outline-gray-1">
					<SettingsRow
						title="Send events to Meta"
						description="Also reads pixel totals back onto your analytics page."
					>
						<Checkbox v-model="checked.enable_facebook" />
					</SettingsRow>
					<template v-if="checked.enable_facebook">
						<SettingsRow
							title="Pixel ID"
							description="The numeric dataset ID in Meta Events Manager → Data sources"
						>
							<FormControl v-model="form.fb_pixel_id" />
						</SettingsRow>
						<SettingsRow
							title="Access token"
							description="A Business System User token with ads_read, ads_management and business_management. Stored encrypted and never shown again."
						>
							<SettingsSecretField
								v-model="secretInputs.fb_access_token"
								v-model:cleared="clearedSecrets.fb_access_token"
								:is-set="Boolean(data?.fb_access_token_is_set)"
								placeholder="Paste the access token"
							/>
						</SettingsRow>
					</template>
				</div>
			</section>

			<section>
				<h3 class="text-base font-medium text-ink-gray-8">Custom tracking scripts</h3>
				<p class="mt-1 text-p-sm text-ink-gray-5">
					Snippets from Google Tag Manager, PostHog, Hotjar and the like, injected on every
					storefront page exactly as you paste them.
				</p>
				<Alert
					class="mt-3"
					theme="amber"
					description="These run unchanged on your storefront. Only paste snippets from a tool you trust."
				/>

				<div class="mt-4 space-y-4">
					<div
						v-for="(row, index) in scripts.rows"
						:key="index"
						class="rounded-5 border border-outline-gray-2 p-3"
					>
						<div class="flex items-center gap-3">
							<FormControl
								v-model="row.title"
								class="flex-1"
								placeholder="What is this snippet?"
							/>
							<Checkbox
								:model-value="row.enabled"
								label="Enabled"
								@update:model-value="(enabled) => (row.enabled = enabled ? 1 : 0)"
							/>
							<Button
								variant="ghost"
								icon-left="lucide-trash-2"
								label="Remove"
								@click="removeScript(index)"
							/>
						</div>
						<FormControl
							v-model="row.script"
							class="mt-3"
							type="textarea"
							:rows="5"
							placeholder="Paste the full snippet, including its own script tags"
						/>
					</div>
					<p v-if="!scripts.rows.length" class="text-p-sm text-ink-gray-5">
						No custom scripts yet.
					</p>
					<Button variant="subtle" icon-left="lucide-plus" label="Add script" @click="addScript" />
				</div>
			</section>

			<SettingsSaveButton
				:loading="save.loading"
				:disabled="!anythingChanged"
				@save="saveAnalyticsSettings()"
			/>
		</div>
	</SettingsBody>
</template>
