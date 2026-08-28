<script setup lang="ts">
import { Badge, Button, FormControl } from "frappe-ui"
import { computed, ref, watch } from "vue"

const props = defineProps<{
	modelValue: string
	/** The server never sends the secret back, only whether one is stored. */
	isSet: boolean
	cleared: boolean
	multiline?: boolean
	placeholder?: string
}>()

const emit = defineEmits<{
	"update:modelValue": [value: string]
	"update:cleared": [value: boolean]
}>()

const editing = ref(false)

// A reload reports what is now stored, so an edit that has been saved folds itself away.
watch(
	() => props.isSet,
	() => {
		editing.value = false
	},
)

const value = computed({
	get: () => props.modelValue,
	set: (next: string) => emit("update:modelValue", next),
})

const showInput = computed(() => editing.value || !props.isSet)

function startReplacing() {
	emit("update:cleared", false)
	editing.value = true
}

function cancelReplacing() {
	emit("update:modelValue", "")
	editing.value = false
}

function clearStoredSecret() {
	emit("update:modelValue", "")
	emit("update:cleared", true)
	editing.value = false
}
</script>

<template>
	<div class="flex flex-col items-end gap-2">
		<template v-if="props.cleared">
			<Badge theme="amber" variant="subtle" label="Removed on save" />
			<Button
				variant="ghost"
				label="Undo"
				@click="emit('update:cleared', false)"
			/>
		</template>

		<template v-else-if="showInput">
			<FormControl
				v-if="props.multiline"
				v-model="value"
				type="textarea"
				:rows="5"
				class="w-72"
				:placeholder="props.placeholder"
			/>
			<FormControl
				v-else
				v-model="value"
				type="password"
				class="w-72"
				:placeholder="props.placeholder"
			/>
			<div class="flex items-center gap-2">
				<Badge v-if="!props.isSet" theme="gray" variant="subtle" label="Not set" />
				<Button v-else variant="ghost" label="Cancel" @click="cancelReplacing" />
			</div>
		</template>

		<template v-else>
			<Badge theme="green" variant="subtle" label="Set" />
			<div class="flex items-center gap-2">
				<Button variant="subtle" label="Replace" @click="startReplacing" />
				<Button variant="ghost" label="Remove" @click="clearStoredSecret" />
			</div>
		</template>
	</div>
</template>
