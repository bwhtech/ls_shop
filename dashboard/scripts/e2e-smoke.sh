#!/usr/bin/env bash
# Dashboard smoke test: walks every route and reports runtime errors + a DOM-text snapshot.
#
# The SPA keeps one page load across route changes, so the console hook is installed once and
# survives the whole walk. Installing it per-route would miss mount-time errors, and
# `agent-browser network console` does not capture page console output at all (verified with a
# canary) — hence the hand-rolled hook.
#
# Usage: ./scripts/e2e-smoke.sh <out-dir> [site] [password]
set -euo pipefail

OUT="${1:?usage: e2e-smoke.sh <out-dir> [site] [password]}"
SITE="${2:-ls_shop-demo.localhost:8010}"
PASSWORD="${3:-Frappe@123}"
SESSION=dash-smoke
export AGENT_BROWSER_DEFAULT_TIMEOUT=45000
mkdir -p "$OUT"

routes=(/store/home /store/orders /store/products /store/inventory /store/analytics
        /storefront/navigation /storefront/footer)

agent-browser --session "$SESSION" open "http://$SITE/login" >/dev/null 2>&1
agent-browser --session "$SESSION" wait --load networkidle >/dev/null 2>&1
agent-browser --session "$SESSION" find label "Email" fill "Administrator" >/dev/null 2>&1
agent-browser --session "$SESSION" find label "Password" fill "$PASSWORD" >/dev/null 2>&1
agent-browser --session "$SESSION" find role button click --name "Continue" >/dev/null 2>&1
agent-browser --session "$SESSION" wait 5000 >/dev/null 2>&1

agent-browser --session "$SESSION" open "http://$SITE/dashboard${routes[0]}" >/dev/null 2>&1
agent-browser --session "$SESSION" wait --load networkidle >/dev/null 2>&1
agent-browser --session "$SESSION" eval --stdin >/dev/null 2>&1 <<'HOOK'
window.__probe = [];
const origError = console.error, origWarn = console.warn;
console.error = (...a) => { window.__probe.push('ERROR: ' + a.map(String).join(' ')); origError(...a); };
console.warn  = (...a) => { window.__probe.push('WARN: '  + a.map(String).join(' ')); origWarn(...a); };
window.addEventListener('error', e => window.__probe.push('UNCAUGHT: ' + e.message));
window.addEventListener('unhandledrejection', e => window.__probe.push('REJECT: ' + e.reason));
'installed'
HOOK

# A broken hook would silently report a clean run, so prove it captures before trusting the walk.
canary=$(agent-browser --session "$SESSION" eval 'console.error("CANARY"); window.__probe.length' 2>&1 | tail -1)
[[ "$canary" == *1* ]] || { echo "FAIL: console hook not capturing (canary=$canary)"; exit 1; }
agent-browser --session "$SESSION" eval 'window.__probe = []; 1' >/dev/null 2>&1

# A route that has not finished switching yields the PREVIOUS route's DOM, and a silent wrong
# capture is worse than no capture. So: push, then poll until both the path matches and the body
# text has actually changed, and mark the route SUSPECT rather than recording the stale page.
previous_text_file=""
for r in "${routes[@]}"; do
	slug=$(echo "$r" | tr '/' '_')
	agent-browser --session "$SESSION" eval "history.pushState({}, '', '/dashboard$r'); window.dispatchEvent(new PopStateEvent('popstate')); 1" >/dev/null 2>&1

	settled=""
	for _attempt in 1 2 3 4 5 6 7 8; do
		agent-browser --session "$SESSION" wait 1000 >/dev/null 2>&1
		agent-browser --session "$SESSION" get text body 2>/dev/null > "$OUT/$slug.txt"
		path=$(agent-browser --session "$SESSION" eval 'location.pathname' 2>/dev/null | tr -d '"' | tail -1)
		[[ "$path" != *"$r" ]] && continue
		if [[ -z "$previous_text_file" ]] || ! cmp -s "$OUT/$slug.txt" "$previous_text_file"; then
			settled=yes
			break
		fi
	done

	chars=$(wc -c < "$OUT/$slug.txt" | tr -d ' ')
	if [[ -n "$settled" ]]; then
		printf "%-26s chars=%s\n" "$r" "$chars"
	else
		printf "%-26s chars=%s  SUSPECT: route never settled, capture may be stale\n" "$r" "$chars"
	fi
	previous_text_file="$OUT/$slug.txt"
done

agent-browser --session "$SESSION" eval 'JSON.stringify(window.__probe, null, 1)' 2>&1 | tail -1 > "$OUT/console.json"
agent-browser --session "$SESSION" close >/dev/null 2>&1
# The probe is written as one JSON line, so counting lines reports 1 no matter how many errors
# there were. Parse the entries instead.
count=$(python3 -c "
import json, sys
raw = open(sys.argv[1]).read().strip()
data = json.loads(raw)
if isinstance(data, str): data = json.loads(data)
print(len(data))
for message, number in __import__('collections').Counter(data).most_common():
    print(f'  {number} x {message[:100]}', file=sys.stderr)
" "$OUT/console.json")
echo "runtime errors captured: $count  ->  $OUT/console.json"
