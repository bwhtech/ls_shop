/** One node of the fulfilment path, exactly as `describe_progress` in api/admin/orders.py builds it. */
export type OrderProgressStep = {
	key: string
	label: string
	state: "done" | "current" | "upcoming"
	at: string | null
	note: string | null
}
