# Modbus Simulator

The simulator exposes a web UI for changing devices and point maps while it is running. Configuration changes are validated, saved, and applied to the live Modbus server without restarting the container.

## Run

The external `ignition_ignition-net` Docker network must already exist.

```powershell
docker compose up --build -d
```

| Instance | Modbus TCP | Web UI |
| --- | --- | --- |
| Interview | `localhost:8052` | http://localhost:8082 |
| Trainer | `localhost:8053` | http://localhost:8083 |

Use **Apply changes** after editing a device or point. The new map takes effect immediately. Existing client connections may need to reconnect after unit IDs or point maps change.

## Configuration

On first startup, each instance's `devices.py` seeds an `instances/<name>/devices.json` file. The JSON file is the persistent configuration from that point forward. Delete it and restart the instance to regenerate it from `devices.py`.

The UI imports and exports both JSON and CSV. CSV is convenient for spreadsheet editing and uses these columns:

```text
device_name,unit_id,zero_based,reverse_word_order,point_type,address,point_name,initial_value,automation_type,automation_settings
```

`point_type` is one of `coils`, `writable_holding_registers`, `holding_registers`, or `input_registers`. Automated registers store their parameters as JSON in `automation_settings`, which preserves nested dew-point definitions.

## Tests

```powershell
$env:PYTHONPATH="$PWD\instances\Interview;$PWD"
.\.venv\Scripts\python.exe -m unittest discover -s tests -v

$env:PYTHONPATH="$PWD\instances\Trainer;$PWD"
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```