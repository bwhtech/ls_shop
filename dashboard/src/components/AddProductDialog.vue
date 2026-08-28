<script setup lang="ts">
import CollectionCombobox from "@/components/CollectionCombobox.vue"
import { errorMessage } from "@/utils/errors"
import {
	Button,
	Dialog,
	ErrorMessage,
	FormControl,
	toast,
	useCall,
} from "frappe-ui"
import { ref } from "vue"

const emit = defineEmits<{ created: [name: string] }>()
const open = defineModel<boolean>("open", { required: true })

const title = ref("")
const collection = ref("")
const options = ref("")
const sizes = ref("")
const price = ref("")
const salePrice = ref("")

const createProduct = useCall<
	{ name: string },
	{
		title: string
		collection: string
		option_attribute: string
		options: string[]
		size_attribute: string
		sizes: string[]
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

function splitValues(value: string) {
	return value
		.split(",")
		.map((entry) => entry.trim())
		.filter(Boolean)
}

function reset() {
	title.value = ""
	collection.value = ""
	options.value = ""
	sizes.value = ""
	price.value = ""
	salePrice.value = ""
}

function submit() {
	createProduct.submit({
		title: title.value,
		collection: collection.value,
		option_attribute: "Colour",
		options: splitValues(options.value),
		size_attribute: "Size",
		sizes: splitValues(sizes.value),
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
				<FormControl
					v-model="options"
					label="Colours"
					description="Comma separated"
					placeholder="Crimson, Teal"
				/>
				<FormControl
					v-model="sizes"
					label="Sizes"
					description="Comma separated"
					placeholder="S, M, L"
				/>
				<div class="grid grid-cols-2 gap-3">
					<FormControl v-model="price" type="number" label="Price" />
					<FormControl v-model="salePrice" type="number" label="Sale price" />
				</div>
				<ErrorMessage :message="createProduct.error?.message" />
				<Button
					class="w-full"
					variant="solid"
					theme="gray"
					icon-left="lucide-plus"
					:loading="createProduct.loading"
					label="Create product"
					@click="submit"
				/>
			</div>
		</template>
	</Dialog>
</template>
