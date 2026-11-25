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
	temperature_period = 42.0 + index
	fan_period = 55.0 + index * 2.0
	fan_power = 1.6 + index * 0.1
	valve_position = sine(7.5, 65.0 + index, 54.0 + load_shift)
	fan_speed = sine(90.0, fan_period, (65.0 + load_shift) * 18.0)
	fan_feedback_addresses = (6, 11, 28, 21, 25, 15, 110, 112)
	fan_ecm_addresses = (80, 82, 84, 86, 88, 90, 106, 108)
	return Equipment(
		name=f"CRAH Unit {index + 1}",
		unit_id=unit_id,
		zero_based=True,
		coils=[
			Coil(0, "Fan/SF_En", True),
			Coil(1, "CHW/CHWV_Auto_Mode", True),
			Coil(7, "Fan/SF_Auto_Mode", True),
			Coil(8, "System/Unit_En_Cmd", True),
			Coil(9, "Alarms/Smoke_Alm"),
			Coil(10, "Alarms/Fan_Flt"),
			Coil(11, "Alarms/Drain_Pan_Lk_Detect"),
			Coil(15, "Alarms/Supervisor_Comm_Loss"),
			Coil(16, "CHW/CHWV_Is_ePIV", True),
			Coil(17, "Alarms/CHWV_Deviating"),
			Coil(18, "Fan/PID/SF_PID_ManMode"),
			Coil(19, "System/Has_LeakDetector", True),
			Coil(20, "System/Has_SmokeDetector", True),
			Coil(21, "Alarms/RAT_Temp_Hi_Alm"),
			Coil(22, "Alarms/RAT_Temp_Lo_Alm"),
			Coil(23, "Alarms/SAT_Temp_Hi_Alm"),
			Coil(24, "Alarms/SAT_Temp_Lo_Alm"),
			Coil(25, "Alarms/Filter_DP_Hi_Alm"),
		],
		writable_holding_registers=[
			WritableRegister(39, "CHW/PID/CHWV_PID_Cycle_Time", 1.0),
			WritableRegister(41, "Supply_Air/SAT_SP", 56.0 + temperature_shift),
			WritableRegister(45, "CHW/PID/CHWV_PID_Kp", 1.0),
			WritableRegister(47, "CHW/PID/CHWV_PID_Ti", 60, data_type="int16"),
			WritableRegister(48, "CHW/PID/CHWV_PID_Td", 0, data_type="int16"),
			WritableRegister(49, "CHW/PID/CHWV_PID_Lo_Lim", 0.0),
			WritableRegister(51, "CHW/PID/CHWV_PID_Hi_Lim", 100.0),
			WritableRegister(55, "CHW/CHWV_Man_Cmd", 0.0),
			WritableRegister(57, "Fan/PID/SF_PID_Cycle_Time", 1.0),
			WritableRegister(63, "Fan/PID/SF_PID_Kp", 1.0),
			WritableRegister(65, "Fan/PID/SF_PID_Ti", 60, data_type="int16"),
			WritableRegister(68, "Fan/PID/SF_PID_Lo_Lim", 20.0),
			WritableRegister(70, "Fan/PID/SF_PID_Hi_Lim", 100.0),
			WritableRegister(72, "Fan/SF_Spd_Man_Cmd", 65.0 + load_shift),
			WritableRegister(75, "Fan/PID/SF_PID_Td", 0, data_type="int16"),
			*[
				WritableRegister(address, f"Fan/Fan_{fan:02d}/ECM_Address", fan, data_type="uint32")
				for fan, address in enumerate(fan_ecm_addresses, start=1)
			],
			WritableRegister(92, "Return_Air/RAT_SP", 75.0 + temperature_shift),
			WritableRegister(120, "Return_Air/RA_Fan_CTRL_SP / RAT_High_Lim_SP", 80.0 + temperature_shift),
			WritableRegister(122, "Return_Air/RA_Fan_CTRL_DB", 2.0),
			WritableRegister(124, "CHW/CHWV_StartUp_Pos", 20.0),
			WritableRegister(150, "CHW/CHWV_Dev_SP", 10.0),
			WritableRegister(152, "Return_Air/RAT_Hi_Dly", 30, data_type="int16"),
			WritableRegister(153, "Return_Air/RAT_Hi_SP", 90.0),
			WritableRegister(155, "Return_Air/RAT_Lo_Dly", 30, data_type="int16"),
			WritableRegister(156, "Return_Air/RAT_Lo_SP", 60.0),
			WritableRegister(158, "Supply_Air/SAT_Hi_Dly", 30, data_type="int16"),
			WritableRegister(159, "Supply_Air/SAT_Hi_SP", 75.0),
			WritableRegister(161, "Supply_Air/SAT_Lo_Dly", 30, data_type="int16"),
			WritableRegister(162, "Supply_Air/SAT_Lo_SP", 45.0),
			WritableRegister(165, "System/Filter_DP_Hi_Alm_SP", 1.0),
			WritableRegister(169, "CHW/CHWV_Max_Flow", 100.0),
		],
		holding_registers=[
			Register(0, "CHW/CHWV_Cmd", valve_position),
			Register(2, "Fan/Fan_Spd_Cmd", sine(5.0, fan_period, 65.0 + load_shift)),
			*[
				Register(address, f"Fan/Fan_{fan:02d}/Fan_Spd_Fdbk", fan_speed, data_type="uint16")
				for fan, address in enumerate(fan_feedback_addresses, start=1)
			],
			Register(31, "Supply_Air/SAT", sine(1.0, temperature_period, 56.0 + temperature_shift)),
			Register(35, "System/Filter_DP", sine(0.02, 32.0 + index, 0.25 + index * 0.025)),
			Register(37, "CHW/CHWV_Fdbk", valve_position),
			Register(78, "Return_Air/RAT", sine(1.5, temperature_period, 75.0 + temperature_shift)),
			Register(126, "CHW/CHW_Flow_Pct", valve_position),
			Register(128, "CHW/CHW_Flow", valve_position),
			*[
				Register(130 + (fan - 1) * 2, f"Fan/Fan_{fan:02d}/Fan_Pwr", sine(0.18, fan_period, fan_power))
				for fan in range(1, 9)
			],
			Register(146, "Fan/Fan_Total_Pwr", sine(1.44, fan_period, fan_power * 8)),
			Register(148, "CHW/CHWV_Deviation", sine(0.0, 60.0, 0.0)),
			Register(164, "System/Filter_DP_Hi_Alm_Dly", sine(0.0, 60.0, 30.0), data_type="int16"),
			Register(167, "System/Delta_T", sine(0.5, temperature_period, 19.0)),
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