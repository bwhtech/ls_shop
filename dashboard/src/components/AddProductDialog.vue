<script setup lang="ts">
import AttributeMultiSelect from "@/components/AttributeMultiSelect.vue"
import CollectionCombobox from "@/components/CollectionCombobox.vue"
import OptionSizeGrid from "@/components/OptionSizeGrid.vue"
import { errorMessage } from "@/utils/errors"
import { buildOptionSizes } from "@/utils/optionSizes"
import {
	Button,
	Dialog,
	ErrorMessage,
	FormControl,
	toast,
	useCall,
} from "frappe-ui"
import { computed, ref } from "vue"

const emit = defineEmits<{ created: [name: string] }>()
const open = defineModel<boolean>("open", { required: true })

const title = ref("")
const collection = ref("")
const options = ref<string[]>([])
const sizes = ref<string[]>([])
const excluded = ref<string[]>([])
const price = ref("")
const salePrice = ref("")

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
	<Dialog v-model:open="open" title="Add product">
		<template #default>
			<div class="space-y-4">
				<FormControl
					v-model="title"
					label="Title"
					required
					placeholder="Merino Wool Jacket"
				/>
				<CollectionCombobox v-model="collection" required />
				<AttributeMultiSelect
					v-model="options"
					attribute="Colour"
					label="Colours"
					placeholder="Pick or type a colour"
					description="Type a new colour to add it"
				/>
				<AttributeMultiSelect
					v-model="sizes"
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
				<p v-if="variantCount" class="text-sm text-ink-gray-5">
					{{ options.length }} {{ options.length === 1 ? "colour" : "colours" }} ·
					{{ variantCount }} {{ variantCount === 1 ? "size" : "sizes" }} will be created
				</p>
				<ErrorMessage :message="gridError || createProduct.error?.message" />
				<Button
					class="w-full"
					variant="solid"
					theme="gray"
					icon-left="lucide-plus"
					:loading="createProduct.loading"
					:disabled="!canSubmit"
					label="Create product"
					@click="submit"
				/>
			</div>
		</template>
	</Dialog>
</template>
