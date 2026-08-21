/**
 * One node of the fulfilment path, exactly as `describe_progress` in api/admin/orders.py builds it.
 * The keys are the fulfilment ladder's own stage keys, which is what lets the stepper share the
 * badge map in utils/format.ts rather than keeping a second opinion about a stage's colour or icon.
 *
 * It lives here rather than in src/types.ts because only the order screen and its stepper speak it.
 */
export type OrderProgressStep = {
	key: string
	label: string
	state: "done" | "current" | "upcoming"
	at: string | null
	note: string | null
}
