import router from "@/router"
import { ref } from "vue"

/** The Add product dialog is mounted by the Products screen, so opening it from anywhere else
 *  means landing there first. */
export const showAddProduct = ref(false)

export async function openAddProduct() {
	await router.push({ name: "Products" })
	showAddProduct.value = true
}
