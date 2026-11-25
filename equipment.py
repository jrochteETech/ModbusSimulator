from dataclasses import dataclass, field
import math
import struct
from typing import Any

from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext


Automation = tuple[str, dict[str, Any]]
REGISTER_WIDTHS = {"float32": 2, "int16": 1, "uint16": 1, "uint32": 2}
INTEGER_REGISTER_LIMITS = {
    "int16": (-32768, 32767),
    "uint16": (0, 65535),
    "uint32": (0, 4294967295),
}


def sine(amplitude: float, period: float, offset: float) -> Automation:
    return "sine", {"amplitude": amplitude, "period": period, "offset": offset}


def linear(duration: float, start: float, end: float, loop: bool = True) -> Automation:
    return "linear", {"duration": duration, "start": start, "end": end, "loop": loop}


def dew_point_fahrenheit(temperature: Automation, humidity: Automation) -> Automation:
    return "dew_point_fahrenheit", {"temperature": temperature, "humidity": humidity}


def float_to_registers(value: float) -> tuple[int, int]:
    """Pack a float32 into two 16-bit registers [MSW, LSW]."""
    packed = struct.pack(">f", value)
    return struct.unpack(">HH", packed)


def register_width(data_type: str) -> int:
    try:
        return REGISTER_WIDTHS[data_type]
    except KeyError as error:
        raise ValueError(f"Unsupported register data type: {data_type!r}") from error


def register_to_values(value: float, data_type: str) -> tuple[int, ...]:
    register_width(data_type)
    if not math.isfinite(value):
        raise ValueError("Register values must be finite")
    if data_type == "float32":
        try:
            return float_to_registers(value)
        except OverflowError as error:
            raise ValueError("Register value is outside the float32 range") from error

    integer_value = round(value)
    minimum, maximum = INTEGER_REGISTER_LIMITS[data_type]
    if not minimum <= integer_value <= maximum:
        raise ValueError(f"Register value must be between {minimum} and {maximum} for {data_type}")
    if data_type == "uint32":
        return integer_value >> 16, integer_value & 0xFFFF
    return (integer_value & 0xFFFF,)


def automation_value(automation: Automation, elapsed: float) -> float:
    kind, settings = automation

    if kind == "sine":
        return settings["offset"] + settings["amplitude"] * math.sin(
            2 * math.pi * elapsed / settings["period"]
        )
    if kind == "linear":
        duration = settings["duration"]
        current = elapsed % duration if settings.get("loop", True) else min(elapsed, duration)
        return settings["start"] + (settings["end"] - settings["start"]) * current / duration
    if kind == "dew_point_fahrenheit":
        temperature_f = automation_value(settings["temperature"], elapsed)
        humidity = max(0.1, min(100.0, automation_value(settings["humidity"], elapsed)))
        temperature_c = (temperature_f - 32.0) * 5.0 / 9.0
        alpha = math.log(humidity / 100.0) + (17.625 * temperature_c) / (
            243.04 + temperature_c
        )
        dew_point_c = 243.04 * alpha / (17.625 - alpha)
        return dew_point_c * 9.0 / 5.0 + 32.0

    raise ValueError(f"Unsupported automation type: {kind}")


@dataclass(frozen=True)
class Register:
    address: int
    name: str
    automation: Automation
    data_type: str = "float32"


@dataclass(frozen=True)
class WritableRegister:
    address: int
    name: str
    initial_value: float
    data_type: str = "float32"


@dataclass(frozen=True)
class Coil:
    address: int
    name: str
    initial_value: bool = False


@dataclass(frozen=True)
class Equipment:
    name: str
    unit_id: int
    zero_based: bool = False
    reverse_word_order: bool = False
    coils: list[Coil] = field(default_factory=list)
    writable_holding_registers: list[WritableRegister] = field(default_factory=list)
    holding_registers: list[Register] = field(default_factory=list)
    input_registers: list[Register] = field(default_factory=list)
    datastore_size: int = 65536

    def make_context(self) -> ModbusSlaveContext:
        context = ModbusSlaveContext(
            co=ModbusSequentialDataBlock(0, [0] * self.datastore_size),
            di=ModbusSequentialDataBlock(0, [0] * self.datastore_size),
            hr=ModbusSequentialDataBlock(0, [0] * self.datastore_size),
            ir=ModbusSequentialDataBlock(0, [0] * self.datastore_size),
            zero_mode=True,
        )
        for coil in self.coils:
            context.setValues(1, self.protocol_address(coil.address), [coil.initial_value])
        for register in self.writable_holding_registers:
            values = register_to_values(register.initial_value, register.data_type)
            if self.reverse_word_order:
                values = values[::-1]
            context.setValues(3, self.protocol_address(register.address), list(values))
        return context

    def protocol_address(self, configured_address: int) -> int:
        address = configured_address if self.zero_based else configured_address - 1
        if address < 0:
            base = 0 if self.zero_based else 1
            raise ValueError(f"{self.name} addresses must start at {base}")
        return address

    def update(self, slave: ModbusSlaveContext, elapsed: float) -> None:
        self._update_registers(slave, 3, self.holding_registers, elapsed)
        self._update_registers(slave, 4, self.input_registers, elapsed)

    def _update_registers(
        self,
        slave: ModbusSlaveContext,
        function_code: int,
        registers: list[Register],
        elapsed: float,
    ) -> None:
        for register in registers:
            values = register_to_values(
                automation_value(register.automation, elapsed), register.data_type
            )
            if self.reverse_word_order:
                values = values[::-1]
            slave.setValues(
                function_code,
                self.protocol_address(register.address),
                list(values),
            )