<script setup lang="ts">
import AttributeMultiSelect from "@/components/AttributeMultiSelect.vue"
import CollectionCombobox from "@/components/CollectionCombobox.vue"
import OptionSizeGrid from "@/components/OptionSizeGrid.vue"
import { errorMessage } from "@/utils/errors"
import { formatMoney } from "@/utils/format"
import { buildOptionSizes, pairKey } from "@/utils/optionSizes"
import {
	Button,
	Dialog,
	ErrorMessage,
	FormControl,
	toast,
	useCall,
} from "frappe-ui"
import { computed, ref } from "vue"

const props = defineProps<{ currency: string }>()
const emit = defineEmits<{ created: [name: string] }>()
const open = defineModel<boolean>("open", { required: true })

const title = ref("")
const collection = ref("")
const options = ref<string[]>([])
const sizes = ref<string[]>([])
const excluded = ref<string[]>([])
const price = ref("")
const salePrice = ref("")
const reviewing = ref(false)
const collectionOpen = ref(false)
const optionsOpen = ref(false)
const sizesOpen = ref(false)

// reka guards only Escape by topmost layer, so one outside click dismisses the
// popover and the dialog both; the dialog yields while a popover owns that click.
const dropdownOpen = computed(
	() => collectionOpen.value || optionsOpen.value || sizesOpen.value,
)

type OptionSizes = { option: string; sizes: string[] }[]

const createProduct = useCall<
	{ name: string },
	{
		title: string
		collection: string
		option_attribute: string
		size_attribute: string
		option_sizes: OptionSizes
		price: string
		sale_price: string
	}
>({
	url: "/api/v2/method/ls_shop.api.admin.catalog.create_product",
	method: "POST",
	immediate: false,
	onSuccess: (product) => {
		open.value = false
		reset()
		emit("created", product.name)
	},
	onError: (error: { message?: string }) =>
		toast.error(errorMessage(error, "Could not create product")),
})

const optionSizes = computed(() =>
	buildOptionSizes(options.value, sizes.value, excluded.value),
)

const variantCount = computed(() =>
	optionSizes.value.reduce((total, row) => total + row.sizes.length, 0),
)

/** Every variant carries the same pair of rates, so the price is resolved once rather than per row. */
const priceLabel = computed(() => {
	const rate = Number.parseFloat(price.value)
	const saleRate = Number.parseFloat(salePrice.value)
	if (saleRate > 0)
		return {
			amount: formatMoney(saleRate, props.currency),
			was: rate > saleRate ? formatMoney(rate, props.currency) : "",
		}
	if (rate > 0) return { amount: formatMoney(rate, props.currency), was: "" }
	return { amount: "No price", was: "" }
})

const variants = computed(() =>
	optionSizes.value.flatMap((row) =>
		row.sizes.map((size) => ({
			key: pairKey(row.option, size),
			option: row.option,
			size,
		})),
	),
)

const emptyOption = computed(
	() => optionSizes.value.find((row) => !row.sizes.length)?.option,
)

const gridError = computed(() =>
	emptyOption.value ? `Pick at least one size for ${emptyOption.value}` : "",
)

const canSubmit = computed(
	() =>
		Boolean(title.value.trim()) &&
		Boolean(collection.value) &&
		variantCount.value > 0 &&
		!emptyOption.value,
)

function reset() {
	reviewing.value = false
	title.value = ""
	collection.value = ""
	options.value = []
	sizes.value = []
	excluded.value = []
	price.value = ""
	salePrice.value = ""
}

function submit() {
	createProduct.submit({
		title: title.value,
		collection: collection.value,
		option_attribute: "Colour",
		size_attribute: "Size",
		option_sizes: optionSizes.value,
		price: price.value,
		sale_price: salePrice.value,
	})
}
</script>

<template>
	<Dialog v-model:open="open" title="Add product" :dismissible="!dropdownOpen">
		<template #default>
			<div class="space-y-4">
				<FormControl
					v-model="title"
					label="Title"
					required
					placeholder="Merino Wool Jacket"
				/>
				<CollectionCombobox
					v-model="collection"
					v-model:open="collectionOpen"
					required
				/>
				<AttributeMultiSelect
					v-model="options"
					v-model:open="optionsOpen"
					attribute="Colour"
					label="Colours"
					placeholder="Pick or type a colour"
					description="Type a new colour to add it"
				/>
				<AttributeMultiSelect
					v-model="sizes"
					v-model:open="sizesOpen"
					attribute="Size"
					label="Sizes"
					placeholder="Pick or type a size"
					description="Type a new size to add it"
				/>
				<OptionSizeGrid
					v-if="options.length && sizes.length"
					v-model="excluded"
					:options="options"
					:sizes="sizes"
				/>
				<div class="grid grid-cols-2 gap-3">
					<FormControl v-model="price" type="number" label="Price" />
					<FormControl v-model="salePrice" type="number" label="Sale price" />
				</div>
				<div v-if="reviewing && variantCount" class="space-y-2">
					<p class="text-sm text-ink-gray-5">
						{{ variantCount }} {{ variantCount === 1 ? "variant" : "variants" }} will be
						created
					</p>
					<ul
						class="max-h-48 divide-y divide-outline-gray-1 overflow-y-auto rounded-4 border border-outline-gray-1"
					>
						<li
							v-for="variant in variants"
							:key="variant.key"
							class="flex items-center justify-between gap-3 px-3 py-2 text-sm"
						>
							<span class="truncate text-ink-gray-8">
								{{ variant.option }} · {{ variant.size }}
							</span>
							<span class="flex shrink-0 items-baseline gap-2">
								<span v-if="priceLabel.was" class="text-xs text-ink-gray-4 line-through">
									{{ priceLabel.was }}
								</span>
								<span class="text-ink-gray-7">{{ priceLabel.amount }}</span>
							</span>
						</li>
					</ul>
				</div>
				<p v-else-if="variantCount" class="text-sm text-ink-gray-5">
					{{ options.length }} {{ options.length === 1 ? "colour" : "colours" }} ·
					{{ variantCount }} {{ variantCount === 1 ? "size" : "sizes" }} will be created
				</p>
				<ErrorMessage :message="gridError || createProduct.error?.message" />
				<div v-if="reviewing" class="flex gap-3">
					<Button class="flex-1" label="Back" @click="reviewing = false" />
					<Button
						class="flex-1"
						variant="solid"
						theme="gray"
						icon-left="lucide-plus"
						:loading="createProduct.loading"
						:disabled="!canSubmit"
						:label="`Create ${variantCount} ${variantCount === 1 ? 'variant' : 'variants'}`"
						@click="submit"
					/>
				</div>
				<Button
					v-else
					class="w-full"
					variant="solid"
					theme="gray"
					icon-left="lucide-list-checks"
					:disabled="!canSubmit"
					label="Review variants"
					@click="reviewing = true"
				/>
			</div>
		</template>
	</Dialog>
</template>
