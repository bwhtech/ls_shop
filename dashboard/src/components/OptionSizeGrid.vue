<script setup lang="ts">
import { buildOptionSizes, pairKey } from "@/utils/optionSizes"
import { Checkbox } from "frappe-ui"
import { computed } from "vue"

const props = defineProps<{ options: string[]; sizes: string[] }>()

const excluded = defineModel<string[]>({ required: true })

const emptyOptions = computed(
	() =>
		new Set(
			buildOptionSizes(props.options, props.sizes, excluded.value)
				.filter((row) => !row.sizes.length)
				.map((row) => row.option),
		),
)

function isSelected(option: string, size: string) {
	return !excluded.value.includes(pairKey(option, size))
}

// Checkbox emits the native value, which is typed loosely enough to include undefined.
function toggle(
	option: string,
	size: string,
	selected: number | boolean | undefined,
) {
	const key = pairKey(option, size)
	excluded.value = selected
		? excluded.value.filter((entry) => entry !== key)
		: [...excluded.value, key]
}
</script>

<template>
	<div>
		<p class="mb-2 text-sm text-ink-gray-5">
			Untick any size you do not carry in a colour.
		</p>
		<div class="overflow-x-auto rounded-4 border border-outline-gray-1">
			<table class="w-full min-w-max border-collapse text-start">
				<thead>
					<tr>
						<th
							class="sticky start-0 z-10 bg-surface-base px-3 py-2 text-xs font-medium text-ink-gray-5"
						>
							Colour
						</th>
						<th
							v-for="size in props.sizes"
							:key="size"
							class="px-3 py-2 text-center text-xs font-medium text-ink-gray-5"
						>
							{{ size }}
						</th>
					</tr>
				</thead>
				<tbody>
					<tr
						v-for="option in props.options"
						:key="option"
						class="border-t border-outline-gray-1"
					>
						<th
							class="sticky start-0 z-10 max-w-40 truncate bg-surface-base px-3 py-2 text-sm font-normal"
							:class="emptyOptions.has(option) ? 'text-ink-red-5' : 'text-ink-gray-8'"
						>
							{{ option }}
						</th>
						<td v-for="size in props.sizes" :key="size" class="px-3 py-2 text-center">
							<Checkbox
								:model-value="isSelected(option, size)"
								:aria-label="`${option} in size ${size}`"
								@update:model-value="toggle(option, size, $event)"
							/>
						</td>
					</tr>
				</tbody>
			</table>
		</div>
	</div>
</template>
