import asyncio
import os
from pathlib import Path
import threading
import time

from pymodbus.datastore import ModbusServerContext
from pymodbus.server import StartAsyncTcpServer

from configuration import ConfigurationStore
from devices import EQUIPMENT
from web_admin import create_app


STEP_SECONDS = 0.5


class SimulatorState:
    def __init__(self, store: ConfigurationStore) -> None:
        self.store = store
        self.context = ModbusServerContext(slaves={}, single=False)
        self._equipment = []
        self._lock = threading.Lock()
        self.reload(store.load())

    def reload(self, equipment) -> None:
        slaves = {item.unit_id: item.make_context() for item in equipment}
        if len(slaves) != len(equipment):
            raise ValueError("Each equipment definition must have a unique unit_id")
        with self._lock:
            self.context._slaves = slaves
            self._equipment = list(equipment)

    def snapshot(self):
        with self._lock:
            return list(self._equipment)

    def apply_document(self, document):
        equipment = self.store.save_document(document)
        self.reload(equipment)
        return self.store.load_document()


def simulation_loop(state: SimulatorState) -> None:
    elapsed = 0.0

    while True:
        for equipment in state.snapshot():
            equipment.update(state.context[equipment.unit_id], elapsed)

        elapsed += STEP_SECONDS
        time.sleep(STEP_SECONDS)


async def main() -> None:
    config_path = Path(os.getenv("CONFIG_PATH", "/app/devices.json"))
    state = SimulatorState(ConfigurationStore(config_path, EQUIPMENT))
    simulation = threading.Thread(
        target=simulation_loop,
        args=(state,),
        daemon=True,
    )
    simulation.start()

    web_port = int(os.getenv("WEB_PORT", "8080"))
    web = create_app(state)
    threading.Thread(
        target=web.run,
        kwargs={"host": "0.0.0.0", "port": web_port, "use_reloader": False},
        daemon=True,
    ).start()

    print("=" * 55)
    print("  Modbus Simulator")
    for equipment in state.snapshot():
        print(f"  Unit {equipment.unit_id}: {equipment.name} (port 502)")
    print(f"  Web UI: http://0.0.0.0:{web_port}")
    print("=" * 55)

    await StartAsyncTcpServer(context=state.context, address=("0.0.0.0", 502))


if __name__ == "__main__":
    asyncio.run(main())