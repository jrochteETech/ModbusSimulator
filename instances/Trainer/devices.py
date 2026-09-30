from equipment import (
	Coil,
	Equipment,
	Register,
	WritableRegister,
	dew_point_fahrenheit,
	linear,
	sine,
)


POWER_METER = Equipment(
	name="Three-phase Power Meter",
	unit_id=1,
	zero_based=False,
	coils=[
		Coil(1, "Meter healthy", True),
	],
	input_registers=[
		Register(1, "Voltage L1", sine(amplitude=2.0, period=12.0, offset=277.0)),
		Register(3, "Voltage L2", sine(amplitude=1.8, period=13.0, offset=277.5)),
		Register(5, "Voltage L3", sine(amplitude=2.2, period=11.0, offset=276.5)),
		Register(7, "Current L1", sine(amplitude=3.5, period=18.0, offset=42.0)),
		Register(9, "Current L2", sine(amplitude=3.0, period=20.0, offset=40.0)),
		Register(11, "Current L3", sine(amplitude=4.0, period=22.0, offset=44.0)),
		Register(13, "Active Power", sine(amplitude=3.0, period=20.0, offset=33.7)),
		Register(15, "Reactive Power", sine(amplitude=1.0, period=24.0, offset=9.1)),
		Register(17, "Apparent Power", sine(amplitude=3.1, period=20.0, offset=34.9)),
		Register(19, "Power Factor", sine(amplitude=0.015, period=30.0, offset=0.965)),
		Register(21, "Frequency", sine(amplitude=0.04, period=15.0, offset=60.0)),
		Register(23, "Energy Import", linear(duration=86400.0, start=250.0, end=1059.0)),
		Register(25, "Voltage L1-L2", sine(amplitude=3.0, period=12.5, offset=480.0)),
		Register(27, "Voltage L2-L3", sine(amplitude=3.2, period=13.5, offset=480.5)),
		Register(29, "Voltage L3-L1", sine(amplitude=3.1, period=11.5, offset=479.5)),
	],
)


CRAH = Equipment(
	name="CRAH Unit",
	unit_id=2,
	zero_based=True,
	reverse_word_order=True,
	coils=[
		Coil(0, "Unit enabled", True),
		Coil(1, "Fan running", True),
		Coil(2, "Cooling active", True),
		Coil(3, "Common alarm"),
		Coil(4, "Dirty filter alarm"),
		Coil(5, "High return temperature alarm"),
		Coil(6, "Low supply temperature alarm"),
		Coil(7, "Fan fault"),
	],
	writable_holding_registers=[
		WritableRegister(2, "Supply Air Temperature Setpoint", 58.0),
	],
	holding_registers=[
		Register(0, "Fan Speed Command", sine(amplitude=5.0, period=60.0, offset=72.0)),
	],
	input_registers=[
		Register(0, "Return Air Temperature", sine(amplitude=1.5, period=45.0, offset=78.0)),
		Register(2, "Supply Air Temperature", sine(amplitude=1.0, period=40.0, offset=58.0)),
		Register(4, "Return Air Humidity", sine(amplitude=2.0, period=55.0, offset=45.0)),
		Register(6, "Supply Air Humidity", sine(amplitude=2.0, period=50.0, offset=52.0)),
		Register(8, "Static Pressure", sine(amplitude=0.08, period=30.0, offset=1.5)),
		Register(10, "Fan Speed Feedback", sine(amplitude=4.8, period=60.0, offset=71.5)),
		Register(12, "Cooling Demand", sine(amplitude=8.0, period=70.0, offset=65.0)),
		Register(14, "CHW Valve Position", sine(amplitude=7.5, period=70.0, offset=64.0)),
		Register(16, "Entering CHW Temperature", sine(amplitude=0.7, period=65.0, offset=44.0)),
		Register(18, "Leaving CHW Temperature", sine(amplitude=1.0, period=65.0, offset=54.0)),
		Register(20, "Filter Differential Pressure", sine(amplitude=0.02, period=35.0, offset=0.35)),
		Register(22, "Cooling Capacity", sine(amplitude=10.0, period=70.0, offset=85.0)),
		Register(24, "Electrical Power", sine(amplitude=2.5, period=60.0, offset=22.0)),
	],
)


THS = Equipment(
	name="THS Gateway",
	unit_id=3,
	datastore_size=256,
	coils=[
		Coil(0, "Sensor enabled", True),
		Coil(1, "Battery Low"),
		Coil(20, "Sensor enabled", True),
		Coil(21, "Battery Low"),
		Coil(40, "Sensor enabled", True),
		Coil(41, "Battery Low"),
	],
	holding_registers=[
		Register(0, "Battery Low Setpoint", sine(amplitude=5.0, period=60.0, offset=3.2)),
		Register(20, "Battery Low Setpoint", sine(amplitude=5.0, period=60.0, offset=3.2)),
		Register(40, "Battery Low Setpoint", sine(amplitude=5.0, period=60.0, offset=3.2)),
	],
	input_registers=[
		Register(0, "Temperature", sine(amplitude=1.5, period=45.0, offset=70.0)),
		Register(2, "Humidity", sine(amplitude=1.0, period=40.0, offset=52.0)),
		Register(4, "Battery Voltage", sine(amplitude=0.5, period=55.0, offset=3.5)),
		Register(6, "Signal Strength", sine(amplitude=10.0, period=50.0, offset=75.0)),
		Register(20, "Temperature", sine(amplitude=1.5, period=45.0, offset=71.0)),
		Register(22, "Humidity", sine(amplitude=1.0, period=40.0, offset=52.5)),
		Register(24, "Battery Voltage", sine(amplitude=0.5, period=55.0, offset=3.6)),
		Register(26, "Signal Strength", sine(amplitude=10.0, period=50.0, offset=80.0)),
		Register(40, "Temperature", sine(amplitude=1.5, period=45.0, offset=72.0)),
		Register(42, "Humidity", sine(amplitude=1.0, period=40.0, offset=53.0)),
		Register(44, "Battery Voltage", sine(amplitude=0.5, period=55.0, offset=3.7)),
		Register(46, "Signal Strength", sine(amplitude=10.0, period=50.0, offset=85.0)),
	],
)


WEATHER_TEMPERATURE = sine(amplitude=12.0, period=240.0, offset=70.0)
WEATHER_HUMIDITY = sine(amplitude=-15.0, period=240.0, offset=60.0)

WEATHER_STATION = Equipment(
	name="Outdoor Weather Station",
	unit_id=4,
	coils=[
		Coil(0, "Station healthy", True),
	],
	input_registers=[
		Register(0, "Outdoor Temperature", WEATHER_TEMPERATURE),
		Register(2, "Relative Humidity", WEATHER_HUMIDITY),
		Register(4, "Wind Speed", sine(amplitude=5.0, period=45.0, offset=8.0)),
		Register(6, "Wind Direction", linear(duration=180.0, start=0.0, end=360.0)),
		Register(8, "Dew Point", dew_point_fahrenheit(WEATHER_TEMPERATURE, WEATHER_HUMIDITY)),
	],
)


EQUIPMENT = [POWER_METER, CRAH, THS, WEATHER_STATION]