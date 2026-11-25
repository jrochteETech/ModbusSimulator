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

Interview seeds `instances/Interview/devices.json` from its `devices.py` on first startup. That host-mounted JSON file preserves its web edits across restarts and redeploys. Delete it and restart Interview to regenerate its defaults.

Trainer runs the code packaged in the image, without host-file overrides. It seeds `/tmp/modbus-trainer/devices.json` inside the container from its packaged `devices.py`. Web edits survive ordinary container restarts, but recreating the container discards them and loads the image's defaults. Host-side Trainer JSON files are not used.

The UI imports and exports both JSON and CSV. CSV is convenient for spreadsheet editing and uses these columns:

```text
device_name,unit_id,zero_based,reverse_word_order,point_type,address,point_name,initial_value,automation_type,automation_settings,data_type
```

`point_type` is one of `coils`, `writable_holding_registers`, `holding_registers`, or `input_registers`. Register `data_type` is `float32` (the default when blank), `int16`, `uint16`, or `uint32`. Integer registers support sine and linear automation. Older CSV exports without the `data_type` column can still be imported. Automated registers store their parameters as JSON in `automation_settings`, which preserves nested dew-point definitions.

## Trainer CRAH_V2

Trainer units 4-13 use the supplied CRAH_V2 map with eight fans and zero-based addresses. Configure the Ignition Modbus connection for zero-based addressing and matching 32-bit word order. Set each UDT's `Device` parameter to the connection name and `UnitID` to the corresponding unit. Telemetry is simulated; changing commands or setpoints does not control the simulated readings or alarms.

The UDT's `RA_Fan_CTRL_SP` and `RAT_High_Lim_SP` both address `HRF120` and therefore share one value. The 33 UDT tags without OPC item paths cannot be mapped.

The CRAH definitions replace the previous Trainer maps directly; no migration is needed. Rebuild the image and recreate Trainer to load them:

```powershell
docker compose up --build --force-recreate -d modbus-trainer
```

This resets all saved Trainer UI customizations. Interview is unchanged. Rebuilding an image without recreating the running Trainer container does not reset its configuration.

## Tests

```powershell
$env:PYTHONPATH="$PWD\instances\Interview;$PWD"
.\.venv\Scripts\python.exe -m unittest discover -s tests -v

$env:PYTHONPATH="$PWD\instances\Trainer;$PWD"
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```