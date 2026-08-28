#!/usr/bin/env bash
# vue-tsc over our own source only.
#
# tsconfig already excludes node_modules and skipLibCheck is on, but skipLibCheck only covers .d.ts:
# vue-tsc still typechecks .vue SFCs imported from a package, so frappe-ui's own experimental
# components (pulled in by the `frappe-ui/experimental` barrel, which we import ListView from) report
# ~106 unresolved `#components/...` errors we cannot fix from here. Failing CI on a dependency's
# internal types is noise, so library lines are printed but only our own errors set the exit code.
set -uo pipefail

output=$(vue-tsc --noEmit --pretty false 2>&1)
own_errors=$(printf '%s\n' "$output" | grep -E '^src/.*error TS' || true)
library_errors=$(printf '%s\n' "$output" | grep -E '^node_modules/.*error TS' || true)

if [[ -n "$own_errors" ]]; then
	printf '%s\n' "$own_errors"
	printf '\n%s error(s) in dashboard/src\n' "$(printf '%s\n' "$own_errors" | wc -l | tr -d ' ')"
	[[ -n "$library_errors" ]] && printf '(%s further error(s) inside node_modules ignored)\n' \
		"$(printf '%s\n' "$library_errors" | wc -l | tr -d ' ')"
	exit 1
fi

printf 'No type errors in dashboard/src\n'
[[ -n "$library_errors" ]] && printf '(%s error(s) inside node_modules ignored)\n' \
	"$(printf '%s\n' "$library_errors" | wc -l | tr -d ' ')"
exit 0
