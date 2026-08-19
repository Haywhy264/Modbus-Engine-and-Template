from __future__ import annotations

from modbus_meter_simulator_v4 import REGISTER_MAP, SENSOR_COUNT, TOTAL_REGISTERS, DummyTagGenerator, MeterSimulator


def test_register_map_has_50_contiguous_tags() -> None:
    assert SENSOR_COUNT == 50
    assert TOTAL_REGISTERS == 50
    assert len(REGISTER_MAP) == 50

    addresses = sorted(meta["address"] for meta in REGISTER_MAP.values())
    assert addresses == list(range(50))


def test_generator_outputs_all_sensor_tags() -> None:
    values = DummyTagGenerator(seed=7).compute_values(12.5)
    assert len(values) == 50
    for index in range(1, 51):
        tag_name = f"sensor_{index:02d}"
        assert tag_name in values
        assert 0 <= values[tag_name] <= 65535


def test_pack_registers_outputs_50_words() -> None:
    simulator = MeterSimulator()
    values = DummyTagGenerator(seed=0).compute_values(0.0)
    regs = simulator._pack_registers(values)

    assert len(regs) == 50
    assert all(0 <= word <= 65535 for word in regs)
