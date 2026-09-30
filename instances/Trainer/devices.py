from equipment import (
	Coil,
	Equipment,
	Register,
	WritableRegister,
	dew_point_fahrenheit,
	linear,
	sine,
)


def make_power_meter(unit_id: int, index: int) -> Equipment:
	voltage = 276.0 + index * 2.5
	current = 38.0 + index * 7.0
	active_power = 31.0 + index * 6.5
	return Equipment(
		name=f"Three-phase Power Meter {index + 1}",
		unit_id=unit_id,
		coils=[Coil(1, "Meter healthy", True)],
		input_registers=[
			Register(1, "Voltage L1", sine(2.0, 12.0 + index, voltage)),
			Register(3, "Voltage L2", sine(1.8, 13.0 + index, voltage + 0.5)),
			Register(5, "Voltage L3", sine(2.2, 11.0 + index, voltage - 0.5)),
			Register(7, "Current L1", sine(3.5, 18.0 + index, current + 2.0)),
			Register(9, "Current L2", sine(3.0, 20.0 + index, current)),
			Register(11, "Current L3", sine(4.0, 22.0 + index, current + 4.0)),
			Register(13, "Active Power", sine(3.0, 20.0 + index, active_power)),
			Register(15, "Reactive Power", sine(1.0, 24.0 + index, 8.0 + index * 1.5)),
			Register(17, "Apparent Power", sine(3.1, 20.0 + index, active_power + 1.2)),
			Register(19, "Power Factor", sine(0.015, 30.0 + index, 0.955 + index * 0.01)),
			Register(21, "Frequency", sine(0.04, 15.0 + index, 59.95 + index * 0.05)),
			Register(23, "Energy Import", linear(86400.0, 250.0 + index * 500.0, 1059.0 + index * 750.0)),
			Register(25, "Voltage L1-L2", sine(3.0, 12.5 + index, 478.0 + index * 4.0)),
			Register(27, "Voltage L2-L3", sine(3.2, 13.5 + index, 478.5 + index * 4.0)),
			Register(29, "Voltage L3-L1", sine(3.1, 11.5 + index, 477.5 + index * 4.0)),
		],
	)


POWER_METERS = [make_power_meter(unit_id, index) for index, unit_id in enumerate(range(1, 4))]


def make_crah(unit_id: int, index: int) -> Equipment:
	temperature_shift = index * 0.6
	load_shift = index * 2.5
	return Equipment(
		name=f"CRAH Unit {index + 1}",
		unit_id=unit_id,
		coils=[
			Coil(1, "Unit enabled", True),
			Coil(2, "Fan running", True),
			Coil(3, "Cooling active", True),
			Coil(4, "Common alarm"),
			Coil(5, "Dirty filter alarm"),
			Coil(6, "High return temperature alarm"),
			Coil(7, "Low supply temperature alarm"),
			Coil(8, "Fan fault"),
		],
		writable_holding_registers=[
			WritableRegister(3, "Supply Air Temperature Setpoint", 56.0 + index * 0.5),
		],
		holding_registers=[
			Register(1, "Fan Speed Command", sine(5.0, 55.0 + index * 2.0, 65.0 + load_shift)),
		],
		input_registers=[
			Register(1, "Return Air Temperature", sine(1.5, 42.0 + index, 75.0 + temperature_shift)),
			Register(3, "Supply Air Temperature", sine(1.0, 38.0 + index, 56.0 + temperature_shift)),
			Register(5, "Return Air Humidity", sine(2.0, 52.0 + index, 42.0 + index * 0.7)),
			Register(7, "Supply Air Humidity", sine(2.0, 48.0 + index, 49.0 + index * 0.6)),
			Register(9, "Static Pressure", sine(0.08, 28.0 + index, 1.2 + index * 0.08)),
			Register(11, "Fan Speed Feedback", sine(4.8, 55.0 + index * 2.0, 64.5 + load_shift)),
			Register(13, "Cooling Demand", sine(8.0, 65.0 + index, 55.0 + load_shift)),
			Register(15, "CHW Valve Position", sine(7.5, 65.0 + index, 54.0 + load_shift)),
			Register(17, "Entering CHW Temperature", sine(0.7, 60.0 + index, 42.0 + index * 0.3)),
			Register(19, "Leaving CHW Temperature", sine(1.0, 60.0 + index, 51.0 + index * 0.4)),
			Register(21, "Filter Differential Pressure", sine(0.02, 32.0 + index, 0.25 + index * 0.025)),
			Register(23, "Cooling Capacity", sine(10.0, 65.0 + index, 70.0 + load_shift)),
			Register(25, "Electrical Power", sine(2.5, 55.0 + index, 16.0 + index * 1.5)),
		],
	)


CRAH_UNITS = [make_crah(unit_id, index) for index, unit_id in enumerate(range(4, 14))]


def make_ths_gateway(unit_id: int, gateway_index: int) -> Equipment:
	coils = []
	holding_registers = []
	input_registers = []

	for sensor_index, register_offset in enumerate(range(0, 300, 20)):
		sensor_number = gateway_index * 15 + sensor_index + 1
		base_address = register_offset + 1
		coils.extend([
			Coil(base_address, f"Sensor {sensor_number} enabled", True),
			Coil(base_address + 1, f"Sensor {sensor_number} battery low"),
		])
		holding_registers.append(
			Register(base_address, f"Sensor {sensor_number} battery low setpoint", sine(0.08, 60.0 + sensor_number, 3.2)),
		)
		input_registers.extend([
			Register(base_address, f"Sensor {sensor_number} temperature", sine(1.0 + sensor_number * 0.03, 40.0 + sensor_number, 67.0 + sensor_number * 0.4)),
			Register(base_address + 2, f"Sensor {sensor_number} humidity", sine(1.0 + sensor_number * 0.02, 36.0 + sensor_number, 43.0 + sensor_number * 0.6)),
			Register(base_address + 4, f"Sensor {sensor_number} battery voltage", sine(0.05, 50.0 + sensor_number, 3.75 - sensor_number * 0.015)),
			Register(base_address + 6, f"Sensor {sensor_number} signal strength", sine(4.0, 45.0 + sensor_number, 90.0 - sensor_number * 1.5)),
		])

	return Equipment(
		name=f"THS Gateway {gateway_index + 1} (Sensors {gateway_index * 15 + 1}-{gateway_index * 15 + 15})",
		unit_id=unit_id,
		datastore_size=320,
		coils=coils,
		holding_registers=holding_registers,
		input_registers=input_registers,
	)


THS_GATEWAYS = [make_ths_gateway(unit_id, index) for index, unit_id in enumerate(range(14, 16))]


WEATHER_TEMPERATURE = sine(amplitude=12.0, period=240.0, offset=70.0)
WEATHER_HUMIDITY = sine(amplitude=-15.0, period=240.0, offset=60.0)

WEATHER_STATION = Equipment(
	name="Outdoor Weather Station",
	unit_id=21,
	coils=[
		Coil(1, "Station healthy", True),
	],
	input_registers=[
		Register(1, "Outdoor Temperature", WEATHER_TEMPERATURE),
		Register(3, "Relative Humidity", WEATHER_HUMIDITY),
		Register(5, "Wind Speed", sine(amplitude=5.0, period=45.0, offset=8.0)),
		Register(7, "Wind Direction", linear(duration=180.0, start=0.0, end=360.0)),
		Register(9, "Dew Point", dew_point_fahrenheit(WEATHER_TEMPERATURE, WEATHER_HUMIDITY)),
	],
)


EQUIPMENT = [*POWER_METERS, *CRAH_UNITS, *THS_GATEWAYS, WEATHER_STATION]