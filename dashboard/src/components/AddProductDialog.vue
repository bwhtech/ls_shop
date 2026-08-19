<script setup lang="ts">
import { FormLabel, Select, createResource } from "frappe-ui"
import { computed, ref } from "vue"

const emit = defineEmits<{ created: [name: string] }>()
const show = defineModel<boolean>({ required: true })

const title = ref("")
const collection = ref("")
const options = ref("")
const sizes = ref("")
const price = ref("")
const salePrice = ref("")

// A store owner cannot be expected to type an Item Group's exact name, so offer the real list
// rather than validating a free-text guess after the fact.
const collections = createResource({
	url: "ls_shop.api.admin.catalog.get_collections",
	auto: true,
})

const collectionOptions = computed(() =>
	(collections.data ?? []).map((name: string) => ({
		label: name,
		value: name,
	})),
)

const createProduct = createResource({
	url: "ls_shop.api.admin.catalog.create_product",
	onSuccess: (data: { name: string }) => {
		show.value = false
		emit("created", data.name)
	},
})

// frappe-ui puts the server-side messages on `messages` and the transport error on `message`;
// showing only one of them renders a bare "ValidationError" with the useful half missing.
const errorMessage = computed(() => {
	const error = createProduct.error
	if (!error) return ""
	return error.messages?.length ? error.messages.join(", ") : error.message
})

function splitValues(value: string) {
	return value
		.split(",")
		.map((entry) => entry.trim())
		.filter(Boolean)
}

function submit() {
	createProduct.error = null
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
	<Dialog v-model="show" title="Add product">
		<template #default>
			<div class="space-y-4">
				<FormControl v-model="title" label="Title" placeholder="Merino Wool Jacket" />
				<div>
					<FormLabel label="Collection" />
					<Select v-model="collection" class="mt-1.5 w-full" :options="collectionOptions" />
				</div>
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
					<FormControl v-model="price" label="Price" type="number" />
					<FormControl v-model="salePrice" label="Sale price" type="number" />
				</div>
				<ErrorMessage :message="errorMessage" />
				<Button
					class="w-full"
					variant="solid"
					:loading="createProduct.loading"
					@click="submit"
				>
					Create product
				</Button>
			</div>
		</template>
	</Dialog>
</template>
