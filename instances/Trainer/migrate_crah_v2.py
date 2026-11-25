import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from configuration import document_from_equipment, equipment_from_document

if __package__:
    from .devices import CRAH_UNITS
else:
    from devices import CRAH_UNITS


def replace_crah_maps(document: dict[str, Any]) -> dict[str, Any]:
    equipment_from_document(document)
    defaults = document_from_equipment(CRAH_UNITS)
    replacements = {device["unit_id"]: device for device in defaults["devices"]}
    present = {int(device["unit_id"]) for device in document["devices"]}
    missing = replacements.keys() - present
    if missing:
        raise ValueError(f"Cannot replace CRAH maps; missing unit IDs: {sorted(missing)}")

    updated = []
    for device in document["devices"]:
        replacement = replacements.get(int(device["unit_id"]))
        if replacement is None:
            updated.append(device)
            continue
        updated.append({
            **device,
            "zero_based": replacement["zero_based"],
            "coils": replacement["coils"],
            "writable_holding_registers": replacement["writable_holding_registers"],
            "holding_registers": replacement["holding_registers"],
            "input_registers": replacement["input_registers"],
        })
    result = {**document, "devices": updated}
    equipment_from_document(result)
    return result


def main() -> None:
    port = os.getenv("WEB_PORT", "8080")
    url = f"http://127.0.0.1:{port}/api/config"
    try:
        with urlopen(url) as response:
            document = json.load(response)
        updated = replace_crah_maps(document)
        request = Request(
            url,
            data=json.dumps(updated).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="PUT",
        )
        with urlopen(request) as response:
            json.load(response)
    except HTTPError as error:
        message = error.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Could not apply CRAH maps: HTTP {error.code}: {message}") from error
    except URLError as error:
        raise SystemExit(f"Could not connect to the Trainer web API: {error.reason}") from error
    print("Applied CRAH_V2 maps to Trainer unit IDs 4-13.")


if __name__ == "__main__":
    main()
