<script setup lang="ts">
import type { ProductSize, ProductVariant } from "@/types"
import { Button, Switch, Tooltip, toast, useCall } from "frappe-ui"
import { computed, ref } from "vue"

const props = defineProps<{ variants: ProductVariant[] }>()
const emit = defineEmits<{ changed: [] }>()

const rates = ref<Record<string, string>>({})
const receiveQuantities = ref<Record<string, string>>({})

function reportError(error: Error) {
	toast.error(error.message)
}

const setPublished = useCall({
	url: "/api/v2/method/ls_shop.api.admin.catalog.set_variant_published",
	method: "POST",
	immediate: false,
	onSuccess: () => emit("changed"),
	onError: reportError,
})

const savePrices = useCall({
	url: "/api/v2/method/ls_shop.api.admin.catalog.save_product_prices",
	method: "POST",
	immediate: false,
	onError: reportError,
})

const receiveStock = useCall({
	url: "/api/v2/method/ls_shop.api.admin.catalog.receive_product_stock",
	method: "POST",
	immediate: false,
	onError: reportError,
})

// Every size sits in one flat table, so prices and stock are readable without expanding a row.
// A product with many colours would make that table unreadable, so past this many sizes the
// groups start collapsed.
const COLLAPSE_ABOVE = 12
const totalSizes = computed(() =>
	props.variants.reduce((total, variant) => total + variant.sizes.length, 0),
)
const collapsed = ref<Record<string, boolean>>({})

function isOpen(variant: ProductVariant) {
	return collapsed.value[variant.name] ?? totalSizes.value <= COLLAPSE_ABOVE
}

function toggle(variant: ProductVariant) {
	collapsed.value[variant.name] = !isOpen(variant)
}

function rateFor(size: ProductSize) {
	return rates.value[size.item_code] ?? size.rate ?? ""
}

const dirty = computed(
	() =>
		Object.keys(rates.value).length > 0 ||
		Object.values(receiveQuantities.value).some(
			(quantity) => Number(quantity) > 0,
		),
)

/** One Save covers the whole table, so an owner repricing a run of sizes clicks once. */
async function saveAll() {
	for (const variant of props.variants) {
		const changedSizes = variant.sizes.filter(
			(size) => size.item_code in rates.value,
		)
		if (changedSizes.length) {
			await savePrices.submit({
				style_attribute_variant: variant.name,
				size_prices: changedSizes.map((size) => ({
					item_code: size.item_code,
					default_rate: rates.value[size.item_code],
				})),
			})
		}

		const received = Object.fromEntries(
			variant.sizes
				.filter((size) => Number(receiveQuantities.value[size.item_code]) > 0)
				.map((size) => [
					size.item_code,
					receiveQuantities.value[size.item_code],
				]),
		)
		if (Object.keys(received).length) {
			await receiveStock.submit({
				style_attribute_variant: variant.name,
				received_quantities: received,
			})
		}
	}

	rates.value = {}
	receiveQuantities.value = {}
	toast.success("Inventory updated")
	emit("changed")
}
</script>

<template>
	<div>
		<table class="w-full">
			<thead>
				<tr class="text-sm text-ink-gray-5">
					<th class="px-4 py-2 text-left font-normal">Option</th>
					<th class="px-2 py-2 text-left font-normal">Size</th>
					<th class="px-2 py-2 text-right font-normal">Price</th>
					<th class="px-2 py-2 text-right font-normal">In stock</th>
					<th class="px-2 py-2 text-right font-normal">Add stock</th>
					<th class="px-4 py-2 text-right font-normal">Live</th>
				</tr>
			</thead>

			<tbody
				v-for="variant in variants"
				:key="variant.name"
				class="border-t border-outline-gray-1"
			>
				<!-- The option and its Live switch span the whole group, so they must sit in the
				     first and last columns of the group's first row - the size cells of that same
				     row go between them, or every later row shifts one column left. -->
				<tr v-for="(size, index) in isOpen(variant) ? variant.sizes : []" :key="size.item_code">
					<td v-if="index === 0" class="px-4 py-2.5 align-top" :rowspan="variant.sizes.length">
						<button type="button" class="flex items-center gap-2.5 text-left" @click="toggle(variant)">
							<img
								v-if="variant.images.length"
								:src="variant.images[0]"
								alt=""
								class="size-8 shrink-0 rounded object-cover"
							/>
							<div
								v-else
								class="grid size-8 shrink-0 place-items-center rounded bg-surface-gray-2 text-xs text-ink-gray-4"
							>
								{{ variant.option.slice(0, 1) }}
							</div>
							<div class="min-w-0">
								<div class="truncate text-base text-ink-gray-9">{{ variant.option }}</div>
								<div v-if="variant.blockers.length" class="text-xs text-ink-amber-6">
									{{ variant.blockers.join(" · ") }}
								</div>
							</div>
						</button>
					</td>

					<td class="px-2 py-1.5 text-base text-ink-gray-7">{{ size.size }}</td>
					<td class="px-2 py-1.5 text-right">
						<input
							:value="rateFor(size)"
							type="number"
							class="w-24 rounded border border-outline-gray-2 bg-surface-base px-2 py-1 text-right text-base text-ink-gray-9"
							@input="rates[size.item_code] = ($event.target as HTMLInputElement).value"
						/>
					</td>
					<td class="px-2 py-1.5 text-right text-base text-ink-gray-7">{{ size.stock }}</td>
					<td class="px-2 py-1.5 text-right">
						<input
							:value="receiveQuantities[size.item_code] ?? ''"
							type="number"
							placeholder="0"
							class="w-20 rounded border border-outline-gray-2 bg-surface-base px-2 py-1 text-right text-base text-ink-gray-9"
							@input="
								receiveQuantities[size.item_code] = (
									$event.target as HTMLInputElement
								).value
							"
						/>
					</td>

					<td
						v-if="index === 0"
						class="px-4 py-2.5 text-right align-top"
						:rowspan="variant.sizes.length"
					>
						<Tooltip
							:text="variant.blockers.join(' · ')"
							:disabled="variant.blockers.length === 0"
						>
							<div class="flex justify-end">
								<Switch
									:model-value="variant.is_published"
									:disabled="!variant.is_published && variant.blockers.length > 0"
									@update:model-value="
										(value: boolean) =>
											setPublished.submit({
												style_attribute_variant: variant.name,
												publish: value ? 1 : 0,
											})
									"
								/>
							</div>
						</Tooltip>
					</td>
				</tr>

				<tr v-if="!isOpen(variant)">
					<td class="px-4 py-2.5">
						<button type="button" class="flex items-center gap-2.5 text-left" @click="toggle(variant)">
							<img
								v-if="variant.images.length"
								:src="variant.images[0]"
								alt=""
								class="size-8 shrink-0 rounded object-cover"
							/>
							<div
								v-else
								class="grid size-8 shrink-0 place-items-center rounded bg-surface-gray-2 text-xs text-ink-gray-4"
							>
								{{ variant.option.slice(0, 1) }}
							</div>
							<div class="truncate text-base text-ink-gray-9">{{ variant.option }}</div>
						</button>
					</td>
					<td class="px-2 py-2.5 text-sm text-ink-gray-5" colspan="4">
						{{ variant.sizes.length }} sizes hidden — click to show
					</td>
					<td class="px-4 py-2.5 text-right">
						<div class="flex justify-end">
							<Switch
								:model-value="variant.is_published"
								:disabled="!variant.is_published && variant.blockers.length > 0"
								@update:model-value="
									(value: boolean) =>
										setPublished.submit({
											style_attribute_variant: variant.name,
											publish: value ? 1 : 0,
										})
								"
							/>
						</div>
					</td>
				</tr>
			</tbody>
		</table>

		<div
			v-if="dirty"
			class="flex items-center justify-end gap-2 border-t border-outline-gray-1 px-4 py-3"
		>
			<span class="mr-auto text-sm text-ink-gray-5">Unsaved inventory changes</span>
			<Button
				label="Discard"
				@click="
					() => {
						rates = {}
						receiveQuantities = {}
					}
				"
			/>
			<Button
				variant="solid"
				theme="gray"
				:loading="savePrices.loading || receiveStock.loading"
				label="Save"
				@click="saveAll"
			/>
		</div>
	</div>
</template>
