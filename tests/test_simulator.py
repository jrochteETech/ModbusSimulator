import tempfile
import unittest
from pathlib import Path

from configuration import (
    ConfigurationStore,
    document_from_csv,
    document_from_equipment,
    document_to_csv,
    equipment_from_document,
)
from devices import EQUIPMENT
from server import SimulatorState
from web_admin import create_app


class ConfigurationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.document = document_from_equipment(EQUIPMENT)

    def test_json_document_round_trip(self) -> None:
        rebuilt = equipment_from_document(self.document)
        self.assertEqual(document_from_equipment(rebuilt), self.document)

    def test_csv_round_trip(self) -> None:
        rebuilt = document_from_csv(document_to_csv(self.document))
        self.assertEqual(rebuilt, self.document)

    def test_api_applies_configuration_to_live_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            state = SimulatorState(ConfigurationStore(Path(directory) / "devices.json", EQUIPMENT))
            client = create_app(state).test_client()

            response = client.get("/api/config")
            self.assertEqual(response.status_code, 200)
            updated = response.get_json()
            updated["devices"][0]["name"] = "Updated from UI"
            updated["devices"][0]["unit_id"] = 247

            response = client.put("/api/config", json=updated)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(state.snapshot()[0].name, "Updated from UI")
            self.assertIn(247, state.context.slaves())

    def test_api_rejects_duplicate_unit_ids(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            state = SimulatorState(ConfigurationStore(Path(directory) / "devices.json", EQUIPMENT))
            client = create_app(state).test_client()
            updated = client.get("/api/config").get_json()
            updated["devices"][1]["unit_id"] = updated["devices"][0]["unit_id"]

            response = client.put("/api/config", json=updated)

            self.assertEqual(response.status_code, 400)
            self.assertIn("used more than once", response.get_json()["error"])

    def test_api_rejects_invalid_automation_before_reload(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            state = SimulatorState(ConfigurationStore(Path(directory) / "devices.json", EQUIPMENT))
            client = create_app(state).test_client()
            updated = client.get("/api/config").get_json()
            updated["devices"][0]["input_registers"][0]["automation"]["period"] = 0

            response = client.put("/api/config", json=updated)

            self.assertEqual(response.status_code, 400)
            self.assertIn("must be greater than zero", response.get_json()["error"])


if __name__ == "__main__":
    unittest.main()