import struct
import unittest

from configuration import (
    document_from_csv,
    document_from_equipment,
    document_to_csv,
    equipment_from_document,
)
from equipment import Equipment, Register, WritableRegister, float_to_registers, sine
from instances.Trainer.devices import CRAH_UNITS


EXPECTED_HOLDING_TYPES = {
    **dict.fromkeys(
        (
            0, 2, 31, 35, 37, 39, 41, 45, 49, 51, 55, 57, 63, 68, 70, 72,
            78, 92, 120, 122, 124, 126, 128, 130, 132, 134, 136, 138, 140,
            142, 144, 146, 148, 150, 153, 156, 159, 162, 165, 167, 169,
        ),
        "float32",
    ),
    **dict.fromkeys((47, 48, 65, 75, 152, 155, 158, 161, 164), "int16"),
    **dict.fromkeys((6, 11, 15, 21, 25, 28, 110, 112), "uint16"),
    **dict.fromkeys((80, 82, 84, 86, 88, 90, 106, 108), "uint32"),
}
EXPECTED_COILS = {0, 1, 7, 8, 9, 10, 11, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25}


def read_float(slave, address: int) -> float:
    return struct.unpack(">f", struct.pack(">HH", *slave.getValues(3, address, 2)))[0]


class CrahV2Tests(unittest.TestCase):
    def test_all_trainer_crahs_match_the_udt_wire_map(self) -> None:
        self.assertEqual([device.unit_id for device in CRAH_UNITS], list(range(4, 14)))
        for device in CRAH_UNITS:
            with self.subTest(unit_id=device.unit_id):
                self.assertTrue(device.zero_based)
                self.assertEqual({coil.address for coil in device.coils}, EXPECTED_COILS)
                registers = [*device.writable_holding_registers, *device.holding_registers]
                self.assertEqual(len(registers), len(EXPECTED_HOLDING_TYPES))
                self.assertEqual(
                    {register.address: register.data_type for register in registers},
                    EXPECTED_HOLDING_TYPES,
                )
                self.assertFalse(device.input_registers)
                by_address = {register.address: register for register in registers}
                for fan, (feedback, ecm) in enumerate(
                    zip((6, 11, 28, 21, 25, 15, 110, 112), (80, 82, 84, 86, 88, 90, 106, 108)),
                    start=1,
                ):
                    self.assertEqual(by_address[feedback].name, f"Fan/Fan_{fan:02d}/Fan_Spd_Fdbk")
                    self.assertEqual(by_address[ecm].name, f"Fan/Fan_{fan:02d}/ECM_Address")
                alias = next(register for register in registers if register.address == 120)
                self.assertIn("RA_Fan_CTRL_SP", alias.name)
                self.assertIn("RAT_High_Lim_SP", alias.name)

    def test_crah_values_use_wire_types_and_keep_writes(self) -> None:
        device = CRAH_UNITS[0]
        slave = device.make_context()
        device.update(slave, 0)

        self.assertTrue(slave.getValues(1, 0, 1)[0])
        self.assertTrue(slave.getValues(1, 8, 1)[0])
        self.assertFalse(slave.getValues(1, 10, 1)[0])
        self.assertAlmostEqual(read_float(slave, 31), 56.0)
        self.assertGreater(slave.getValues(3, 6, 1)[0], 1000)
        self.assertEqual(slave.getValues(3, 80, 2), [0, 1])
        fan_power = sum(read_float(slave, address) for address in range(130, 146, 2))
        self.assertAlmostEqual(read_float(slave, 146), fan_power, places=4)

        slave.setValues(3, 41, list(float_to_registers(60.5)))
        slave.setValues(3, 47, [123])
        device.update(slave, 15)
        self.assertNotAlmostEqual(read_float(slave, 31), 56.0)
        self.assertAlmostEqual(read_float(slave, 41), 60.5)
        self.assertEqual(slave.getValues(3, 47, 1), [123])

    def test_integer_registers_round_trip_and_reverse_only_32_bit_words(self) -> None:
        device = Equipment(
            name="Typed registers",
            unit_id=1,
            zero_based=True,
            reverse_word_order=True,
            writable_holding_registers=[
                WritableRegister(0, "Unsigned 32", 0x12345678, data_type="uint32"),
                WritableRegister(2, "Signed 16", -3, data_type="int16"),
            ],
            holding_registers=[
                Register(3, "Unsigned 16", sine(0, 60, 1500), data_type="uint16"),
            ],
        )
        document = document_from_equipment([device])
        self.assertEqual(document_from_equipment(equipment_from_document(document)), document)
        self.assertEqual(document_from_csv(document_to_csv(document)), document)

        rebuilt = equipment_from_document(document)[0]
        slave = rebuilt.make_context()
        rebuilt.update(slave, 0)
        self.assertEqual(slave.getValues(3, 0, 4), [0x5678, 0x1234, 0xFFFD, 1500])

    def test_invalid_integer_values_and_overlapping_widths_are_rejected(self) -> None:
        cases = [
            Equipment("Bad initial", 1, zero_based=True, writable_holding_registers=[
                WritableRegister(0, "Value", 65536, data_type="uint16"),
            ]),
            Equipment("Fractional initial", 1, zero_based=True, writable_holding_registers=[
                WritableRegister(0, "Value", 1.5, data_type="int16"),
            ]),
            Equipment("Bad automation", 1, zero_based=True, holding_registers=[
                Register(0, "Value", sine(20, 60, 65530), data_type="uint16"),
            ]),
            Equipment("Overlap", 1, zero_based=True, holding_registers=[
                Register(0, "Float", sine(0, 60, 1)),
                Register(1, "Integer", sine(0, 60, 1), data_type="uint16"),
            ]),
        ]
        for device in cases:
            with self.subTest(device=device.name), self.assertRaises(ValueError):
                equipment_from_document(document_from_equipment([device]))

    def test_legacy_csv_still_imports_float_registers(self) -> None:
        content = (
            "device_name,unit_id,zero_based,reverse_word_order,point_type,address,"
            "point_name,initial_value,automation_type,automation_settings\n"
            "Legacy,1,false,false,writable_holding_registers,1,Setpoint,42,,\n"
        )
        device = equipment_from_document(document_from_csv(content))[0]
        self.assertEqual(device.writable_holding_registers[0].data_type, "float32")


if __name__ == "__main__":
    unittest.main()
