<script setup lang="ts">
import {
	Avatar,
	Button,
	FileUploader,
	SettingsBody,
	SettingsHeader,
	TextInput,
	toast,
	useCall,
} from "frappe-ui"
import { computed, reactive, watch } from "vue"

type Profile = {
	name: string
	email: string
	full_name: string
	first_name: string
	last_name: string
	user_image: string | null
}

const profile = useCall<Profile>({
	url: "/api/v2/method/ls_shop.api.admin.settings.get_profile",
})

const form = reactive({ first_name: "", last_name: "" })

watch(
	() => profile.data,
	(data) => {
		if (!data) return
		form.first_name = data.first_name ?? ""
		form.last_name = data.last_name ?? ""
	},
	{ immediate: true },
)

const save = useCall<Profile>({
	url: "/api/v2/method/ls_shop.api.admin.settings.save_profile",
	method: "POST",
	immediate: false,
	onSuccess: () => profile.reload(),
	onError: (error: Error) => toast.error(error.message),
})

const nameChanged = computed(
	() =>
		!!profile.data &&
		(form.first_name !== (profile.data.first_name ?? "") ||
			form.last_name !== (profile.data.last_name ?? "")),
)

// Gameplan saves the name on blur rather than behind a button, so the field feels like the
// record itself rather than a form you have to remember to submit.
function saveName() {
	if (!nameChanged.value) return
	save.submit({ ...form })
}
</script>

<template>
	<SettingsHeader>
		<h2 class="text-lg font-semibold text-ink-gray-8">Profile</h2>
	</SettingsHeader>

	<SettingsBody>
		<div v-if="profile.data" class="space-y-8 pt-6">
			<div class="flex items-center gap-4">
				<FileUploader
					:file-types="['image/*']"
					:upload-args="{ private: false }"
					@success="
						(file: { file_url: string }) => {
							save.submit({ user_image: file.file_url })
							toast.success('Profile picture updated')
						}
					"
				>
					<template #default="{ openFileSelector, uploading }">
						<button
							type="button"
							class="rounded-full focus:outline-none"
							aria-label="Change profile picture"
							:disabled="uploading"
							@click="openFileSelector"
						>
							<Avatar
								size="3xl"
								class="!size-16"
								:image="profile.data.user_image ?? undefined"
								:label="profile.data.full_name"
							/>
						</button>
					</template>
				</FileUploader>

				<div>
					<div class="text-base font-medium text-ink-gray-8">Profile picture</div>
					<p class="text-p-sm text-ink-gray-5">Helps your team recognise you</p>
				</div>
			</div>

			<div class="grid gap-6 sm:grid-cols-2">
				<TextInput
					v-model="form.first_name"
					label="First name"
					class="w-full"
					:disabled="save.loading"
					@blur="saveName"
				/>
				<TextInput
					v-model="form.last_name"
					label="Last name"
					class="w-full"
					:disabled="save.loading"
					@blur="saveName"
				/>
			</div>

			<div>
				<TextInput
					:model-value="profile.data.email"
					label="Email"
					class="w-full"
					disabled
				/>
				<p class="mt-1.5 text-p-sm text-ink-gray-5">
					Your sign-in address. Changing it is a Desk admin task.
				</p>
			</div>
		</div>
	</SettingsBody>
</template>
