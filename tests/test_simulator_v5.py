from __future__ import annotations

from modbus_meter_simulator_v5 import REGISTER_MAP, SENSOR_COUNT, TOTAL_REGISTERS, DummyTagGenerator, MeterSimulator


def test_register_map_has_500_contiguous_tags() -> None:
    assert SENSOR_COUNT == 500
    assert TOTAL_REGISTERS == 500
    assert len(REGISTER_MAP) == 500

    addresses = sorted(meta["address"] for meta in REGISTER_MAP.values())
    assert addresses == list(range(500))


def test_generator_outputs_all_sensor_tags() -> None:
    values = DummyTagGenerator(seed=7).compute_values(12.5)
    assert len(values) == 500
    for index in range(1, 501):
        tag_name = f"sensor_{index:03d}"
        assert tag_name in values
        assert 0 <= values[tag_name] <= 65535


def test_pack_registers_outputs_500_words() -> None:
    simulator = MeterSimulator()
    values = DummyTagGenerator(seed=0).compute_values(0.0)
    regs = simulator._pack_registers(values)

    assert len(regs) == 500
    assert all(0 <= word <= 65535 for word in regs)
