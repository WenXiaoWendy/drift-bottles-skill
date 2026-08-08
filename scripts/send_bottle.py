#!/usr/bin/env python3
import json
import os
import sys
import urllib.error
import urllib.request


DEFAULT_BASE_URL = "https://galatea.abysslumina.com"
PATH = "/api/public/drift-bottle-application"


def call(payload: dict) -> dict:
    base_url = os.environ.get("GALATEA_GARDEN_URL", DEFAULT_BASE_URL).rstrip("/")
    request = urllib.request.Request(
        f"{base_url}{PATH}",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "galatea-garden-drift-bottle-skill/1"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            detail = json.loads(exc.read().decode("utf-8")).get("detail")
        except (ValueError, AttributeError):
            detail = None
        raise RuntimeError(str(detail or f"shore returned HTTP {exc.code}")) from None
    except urllib.error.URLError as exc:
        raise RuntimeError(f"could not reach the Garden shore: {exc.reason}") from None


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in {"prepare", "submit"}:
        print("usage: send_bottle.py {prepare|submit}", file=sys.stderr)
        return 2
    if sys.argv[1] == "prepare":
        print(json.dumps(call({"action": "prepare"}), ensure_ascii=False, indent=2))
        return 0
    try:
        value = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"invalid JSON input: {exc}", file=sys.stderr)
        return 2
    if not isinstance(value, dict):
        print("submit input must be one JSON object", file=sys.stderr)
        return 2
    required = {"challenge_id", "confirmation_code", "applicant_name", "email", "body"}
    missing = sorted(required - value.keys())
    if missing:
        print(f"missing required fields: {', '.join(missing)}", file=sys.stderr)
        return 2
    try:
        result = call({"action": "submit", **{key: value[key] for key in required}})
    except RuntimeError as exc:
        print(f"bottle could not be sent: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({key: result.get(key) for key in ("accepted", "receipt_id", "message")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

