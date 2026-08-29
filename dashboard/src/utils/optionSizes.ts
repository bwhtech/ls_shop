/** Colour + size pairs, keyed for a Set. A NUL cannot appear in an attribute value, so it joins safely. */
export function pairKey(option: string, size: string) {
	return `${option}\u0000${size}`
}

/**
 * The grid stores what the owner UNticked, not what they ticked, so a colour or size added later
 * arrives selected everywhere without a second pass over the existing choices.
 */
export function buildOptionSizes(
	options: string[],
	sizes: string[],
	excluded: string[],
) {
	const dropped = new Set(excluded)
	return options.map((option) => ({
		option,
		sizes: sizes.filter((size) => !dropped.has(pairKey(option, size))),
	}))
}
