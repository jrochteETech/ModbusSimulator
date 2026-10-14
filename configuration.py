import csv
from io import StringIO
import json
import math
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from equipment import Coil, Equipment, Register, WritableRegister


CONFIG_VERSION = 1
CSV_FIELDS = [
    "device_name", "unit_id", "zero_based", "reverse_word_order", "point_type",
    "address", "point_name", "initial_value", "automation_type", "automation_settings",
]


def automation_to_dict(automation: tuple[str, dict[str, Any]]) -> dict[str, Any]:
    kind, settings = automation
    return {
        "type": kind,
        **{
            key: automation_to_dict(value)
            if key in {"temperature", "humidity"}
            else value
            for key, value in settings.items()
        },
    }


def automation_from_dict(data: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    settings = {
        key: automation_from_dict(value)
        if key in {"temperature", "humidity"}
        else value
        for key, value in data.items()
        if key != "type"
    }
    return str(data["type"]), settings


def equipment_to_dict(equipment: Equipment) -> dict[str, Any]:
    return {
        "name": equipment.name,
        "unit_id": equipment.unit_id,
        "zero_based": equipment.zero_based,
        "reverse_word_order": equipment.reverse_word_order,
        "coils": [
            {"address": item.address, "name": item.name, "initial_value": item.initial_value}
            for item in equipment.coils
        ],
        "writable_holding_registers": [
            {"address": item.address, "name": item.name, "initial_value": item.initial_value}
            for item in equipment.writable_holding_registers
        ],
        "holding_registers": [
            {"address": item.address, "name": item.name, "automation": automation_to_dict(item.automation)}
            for item in equipment.holding_registers
        ],
        "input_registers": [
            {"address": item.address, "name": item.name, "automation": automation_to_dict(item.automation)}
            for item in equipment.input_registers
        ],
    }


def equipment_from_dict(data: dict[str, Any]) -> Equipment:
    return Equipment(
        name=str(data["name"]),
        unit_id=int(data["unit_id"]),
        zero_based=bool(data.get("zero_based", False)),
        reverse_word_order=bool(data.get("reverse_word_order", False)),
        coils=[Coil(int(item["address"]), str(item["name"]), bool(item.get("initial_value", False))) for item in data.get("coils", [])],
        writable_holding_registers=[
            WritableRegister(int(item["address"]), str(item["name"]), float(item.get("initial_value", 0)))
            for item in data.get("writable_holding_registers", [])
        ],
        holding_registers=[
            Register(int(item["address"]), str(item["name"]), automation_from_dict(item["automation"]))
            for item in data.get("holding_registers", [])
        ],
        input_registers=[
            Register(int(item["address"]), str(item["name"]), automation_from_dict(item["automation"]))
            for item in data.get("input_registers", [])
        ],
    )


def document_from_equipment(equipment: list[Equipment]) -> dict[str, Any]:
    return {"version": CONFIG_VERSION, "devices": [equipment_to_dict(item) for item in equipment]}


def equipment_from_document(document: dict[str, Any]) -> list[Equipment]:
    if document.get("version") != CONFIG_VERSION:
        raise ValueError(f"Unsupported configuration version: {document.get('version')}")
    devices = [equipment_from_dict(item) for item in document.get("devices", [])]
    validate_equipment(devices)
    return devices


def document_to_csv(document: dict[str, Any]) -> str:
    equipment_from_document(document)
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    for device in document["devices"]:
        common = {
            "device_name": device["name"],
            "unit_id": device["unit_id"],
            "zero_based": str(device.get("zero_based", False)).lower(),
            "reverse_word_order": str(device.get("reverse_word_order", False)).lower(),
        }
        wrote_point = False
        for point_type in ("coils", "writable_holding_registers", "holding_registers", "input_registers"):
            for point in device.get(point_type, []):
                automation = point.get("automation")
                writer.writerow({
                    **common,
                    "point_type": point_type,
                    "address": point["address"],
                    "point_name": point["name"],
                    "initial_value": point.get("initial_value", ""),
                    "automation_type": automation.get("type", "") if automation else "",
                    "automation_settings": json.dumps(
                        {key: value for key, value in automation.items() if key != "type"},
                        separators=(",", ":"),
                    ) if automation else "",
                })
                wrote_point = True
        if not wrote_point:
            writer.writerow(common)
    return output.getvalue()


def document_from_csv(content: str) -> dict[str, Any]:
    devices: dict[int, dict[str, Any]] = {}
    reader = csv.DictReader(StringIO(content))
    if reader.fieldnames != CSV_FIELDS:
        raise ValueError("CSV columns do not match the exported device format")
    for row_number, row in enumerate(reader, start=2):
        try:
            unit_id = int(row["unit_id"])
            device = devices.setdefault(unit_id, {
                "name": row["device_name"],
                "unit_id": unit_id,
                "zero_based": _csv_bool(row["zero_based"]),
                "reverse_word_order": _csv_bool(row["reverse_word_order"]),
                "coils": [],
                "writable_holding_registers": [],
                "holding_registers": [],
                "input_registers": [],
            })
            if device["name"] != row["device_name"]:
                raise ValueError(f"unit {unit_id} has inconsistent device names")
            point_type = row["point_type"]
            if not point_type:
                continue
            if point_type not in {"coils", "writable_holding_registers", "holding_registers", "input_registers"}:
                raise ValueError(f"unknown point type {point_type}")
            point: dict[str, Any] = {"address": int(row["address"]), "name": row["point_name"]}
            if point_type == "coils":
                point["initial_value"] = _csv_bool(row["initial_value"])
            elif point_type == "writable_holding_registers":
                point["initial_value"] = float(row["initial_value"])
            else:
                settings = json.loads(row["automation_settings"] or "{}")
                point["automation"] = {"type": row["automation_type"], **settings}
            device[point_type].append(point)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            raise ValueError(f"CSV row {row_number}: {error}") from error
    document = {"version": CONFIG_VERSION, "devices": list(devices.values())}
    equipment_from_document(document)
    return document


def _csv_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized not in {"true", "false", "1", "0", "yes", "no"}:
        raise ValueError(f"invalid boolean value {value!r}")
    return normalized in {"true", "1", "yes"}


def validate_equipment(devices: list[Equipment]) -> None:
    unit_ids: set[int] = set()
    for device in devices:
        if not device.name.strip():
            raise ValueError("Device names cannot be empty")
        if not 1 <= device.unit_id <= 247:
            raise ValueError(f"{device.name}: unit ID must be between 1 and 247")
        if device.unit_id in unit_ids:
            raise ValueError(f"Unit ID {device.unit_id} is used more than once")
        unit_ids.add(device.unit_id)

        _validate_points(device, "coils", device.coils, width=1)
        _validate_points(
            device,
            "holding registers",
            [*device.writable_holding_registers, *device.holding_registers],
            width=2,
        )
        _validate_points(device, "input registers", device.input_registers, width=2)
        for register in [*device.holding_registers, *device.input_registers]:
            _validate_automation(register.automation, f"{device.name}: {register.name}")


def _validate_points(device: Equipment, group_name: str, points: list[Any], width: int) -> None:
    occupied: set[int] = set()
    for point in points:
        if not point.name.strip():
            raise ValueError(f"{device.name}: point names cannot be empty")
        start = device.protocol_address(point.address)
        span = set(range(start, start + width))
        if max(span) >= device.datastore_size:
            raise ValueError(f"{device.name}: address {point.address} exceeds the datastore size")
        if occupied & span:
            raise ValueError(f"{device.name}: address {point.address} overlaps another {group_name} point")
        occupied.update(span)


def _validate_automation(automation: tuple[str, dict[str, Any]], label: str) -> None:
    kind, settings = automation
    required = {
        "sine": ("amplitude", "period", "offset"),
        "linear": ("duration", "start", "end"),
        "dew_point_fahrenheit": ("temperature", "humidity"),
    }
    if kind not in required:
        raise ValueError(f"{label}: unsupported automation type {kind!r}")
    missing = [key for key in required[kind] if key not in settings]
    if missing:
        raise ValueError(f"{label}: missing automation setting {missing[0]!r}")
    if kind == "dew_point_fahrenheit":
        _validate_automation(settings["temperature"], f"{label} temperature")
        _validate_automation(settings["humidity"], f"{label} humidity")
        return
    for key in required[kind]:
        value = settings[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(f"{label}: automation setting {key!r} must be a finite number")
    duration_key = "period" if kind == "sine" else "duration"
    if settings[duration_key] <= 0:
        raise ValueError(f"{label}: {duration_key} must be greater than zero")


class ConfigurationStore:
    def __init__(self, path: Path, defaults: list[Equipment]) -> None:
        self.path = path
        if not path.exists():
            self.save(defaults)

    def load_document(self) -> dict[str, Any]:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def load(self) -> list[Equipment]:
        return equipment_from_document(self.load_document())

    def save_document(self, document: dict[str, Any]) -> list[Equipment]:
        devices = equipment_from_document(document)
        self.save(devices)
        return devices

    def save(self, devices: list[Equipment]) -> None:
        validate_equipment(devices)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        document = document_from_equipment(devices)
        with NamedTemporaryFile("w", encoding="utf-8", dir=self.path.parent, delete=False) as temporary:
            json.dump(document, temporary, indent=2)
            temporary.write("\n")
            temporary_path = Path(temporary.name)
        temporary_path.replace(self.path)