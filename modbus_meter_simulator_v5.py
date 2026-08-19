#!/usr/bin/env python3
"""
Modbus TCP dummy sensor simulator for SiteSee2 automated testing (Version 5).

Version 5 additions
-------------------
- Simulates 500 dummy sensor tags together in one update cycle
- Uses 500 contiguous holding registers (FC03), mirrored to input registers (FC04)
- Keeps V4 external-client behavior (0.0.0.0 default bind + connected IP tracking)

Register map
------------
- Tags: sensor_001 ... sensor_500
- Address range: 0..499
- Type: uint16 (1 word per tag)
- Unit: raw
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import math
import signal
import sys
import time
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

from pymodbus import ModbusDeviceIdentification
from pymodbus.datastore import (
    ModbusDeviceContext,
    ModbusSequentialDataBlock,
    ModbusServerContext,
)
from pymodbus.server.requesthandler import ServerRequestHandler
from pymodbus.server.server import ModbusTcpServer

logger = logging.getLogger(__name__)

CLIENT_IPS_TOKEN = "CLIENT_IPS="

SENSOR_COUNT: int = 500
TOTAL_REGISTERS: int = SENSOR_COUNT
CYCLE_PERIOD_S: float = 60.0
_BLOCK_START: int = 1
_REGISTER_START: int = 0


def _build_register_map() -> Dict[str, Dict]:
    register_map: Dict[str, Dict] = {}
    for idx in range(SENSOR_COUNT):
        name = f"sensor_{idx + 1:03d}"
        register_map[name] = {
            "address": idx,
            "count": 1,
            "type": "uint16",
            "unit": "raw",
            "description": f"Dummy sensor tag {idx + 1}",
        }
    return register_map


REGISTER_MAP: Dict[str, Dict] = _build_register_map()


@dataclass
class Stats:
    """Monotonically-increasing simulator counters."""

    request_count: int = 0
    connection_count: int = 0
    error_count: int = 0


class DummyTagGenerator:
    """Produces deterministic, repeatable values for 500 dummy sensor tags."""

    def __init__(self, seed: int = 0, tag_count: int = SENSOR_COUNT) -> None:
        self._seed = seed
        self._tag_count = tag_count
        self._phase_offset: float = (seed % 360) * (math.pi / 180.0)

    def compute_values(self, t: float) -> Dict[str, int]:
        phase = (t / CYCLE_PERIOD_S) * 2.0 * math.pi + self._phase_offset
        values: Dict[str, int] = {}

        for idx in range(self._tag_count):
            tag_name = f"sensor_{idx + 1:03d}"
            base = 1_000.0 + (idx * 20.0)
            amplitude = 120.0 + ((idx % 7) * 15.0)
            harmonic = 18.0 * math.sin((phase * 3.0) + (idx * 0.31))
            raw = base + amplitude * math.sin(phase + (idx * 0.19)) + harmonic
            clamped = max(0, min(65_535, int(round(raw))))
            values[tag_name] = clamped

        return values


class MeterDataBlock(ModbusSequentialDataBlock):
    """Holding-register block with DEBUG-level logging on client access."""

    def __init__(self, address: int, values: List[int], stats: Stats) -> None:
        super().__init__(address, values)
        self._base_address = address
        self._stats = stats

    def getValues(self, address: int, count: int = 1) -> List[int]:  # noqa: N802
        parent_get = getattr(super(), "getValues", None)
        if callable(parent_get):
            result = parent_get(address, count)
        else:
            start = address - self._base_address
            end = start + count
            result = list(self.simdata[0].values[start:end])
        logger.debug("HR read   block_addr=%d  count=%d  values=%s", address, count, result)
        return result

    def setValues(self, address: int, values: List[int]) -> None:  # noqa: N802
        parent_set = getattr(super(), "setValues", None)
        if callable(parent_set):
            parent_set(address, values)
        else:
            if isinstance(values, int):
                values = [values]
            start = address - self._base_address
            end = start + len(values)
            backing = self.simdata[0].values
            if end > len(backing):
                backing.extend([0] * (end - len(backing)))
            backing[start:end] = list(values)
        logger.debug("HR write  block_addr=%d  values=%s", address, values)

    def update_internal(self, address: int, values: List[int]) -> None:
        self.setValues(address, values)


class IPTrackingServerRequestHandler(ServerRequestHandler):
    """Request handler that exposes peer IP changes to the owning server."""

    def _peer_ip(self) -> str:
        transport = getattr(self, "transport", None)
        if transport is None:
            return "unknown"
        peer = transport.get_extra_info("peername")
        if isinstance(peer, tuple) and peer:
            return str(peer[0])
        if peer:
            return str(peer)
        return "unknown"

    def callback_connected(self) -> None:
        super().callback_connected()
        self.server.notify_connection_event(self.unique_id, True, self._peer_ip())

    def callback_disconnected(self, exc: Exception | None) -> None:
        peer_ip = self._peer_ip()
        super().callback_disconnected(exc)
        self.server.notify_connection_event(self.unique_id, False, peer_ip)


class IPTrackingModbusTcpServer(ModbusTcpServer):
    """Modbus TCP server with per-connection peer-IP tracking."""

    def __init__(
        self,
        *args,
        on_client_event: Callable[[str, bool], None] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._on_client_event = on_client_event
        self._connection_ip_by_id: dict[object, str] = {}

    def callback_new_connection(self) -> IPTrackingServerRequestHandler:
        return IPTrackingServerRequestHandler(
            self,
            self.trace_packet,
            self.trace_pdu,
            self.trace_connect,
        )

    def notify_connection_event(self, connection_id: object, connected: bool, peer_ip: str) -> None:
        ip = peer_ip
        if connected:
            self._connection_ip_by_id[connection_id] = ip
        else:
            ip = self._connection_ip_by_id.pop(connection_id, peer_ip)

        if self._on_client_event is not None:
            self._on_client_event(ip, connected)


class MeterSimulator:
    """500-tag Modbus TCP dummy sensor simulator (Version 5)."""

    DEFAULT_HOST: str = "0.0.0.0"
    DEFAULT_PORT: int = 5023
    DEFAULT_UNIT_ID: int = 1
    DEFAULT_SEED: int = 0
    DEFAULT_UPDATE_INTERVAL_MS: int = 100
    DEFAULT_DISPLAY_INTERVAL_S: float = 1.0

    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        unit_id: int = DEFAULT_UNIT_ID,
        seed: int = DEFAULT_SEED,
        update_interval_ms: int = DEFAULT_UPDATE_INTERVAL_MS,
        show_values: bool = True,
        display_interval_s: float = DEFAULT_DISPLAY_INTERVAL_S,
    ) -> None:
        self.host: str = host
        self.port: int = port
        self.unit_id: int = unit_id
        self.stats: Stats = Stats()
        self._generator: DummyTagGenerator = DummyTagGenerator(seed)
        self._update_interval: float = update_interval_ms / 1_000.0
        self._seed: int = seed
        self._show_values: bool = show_values
        self._display_interval: float = max(0.1, display_interval_s)
        self._last_display_ts: float = 0.0
        self._datablock: Optional[MeterDataBlock] = None
        self._ir_block: Optional[ModbusSequentialDataBlock] = None
        self._update_task: Optional[asyncio.Task] = None
        self._server: Optional[IPTrackingModbusTcpServer] = None
        self._running: bool = False
        self._ip_connection_counts: dict[str, int] = {}

    async def _on_runtime_access(
        self,
        func_code: int,
        _start_address: int,
        _address: int,
        _count: int,
        current_registers: list[int],
        set_values: list[int] | list[bool] | None,
    ) -> None:
        if set_values is not None:
            return
        if func_code not in (3, 4):
            return

        registers = self._pack_registers(self._generator.compute_values(time.time()))
        current_registers[:TOTAL_REGISTERS] = registers

    async def start(self) -> None:
        self._running = True

        initial = self._pack_registers(self._generator.compute_values(time.time()))
        self._datablock = MeterDataBlock(_BLOCK_START, initial, self.stats)
        self._ir_block = ModbusSequentialDataBlock(_BLOCK_START, list(initial))

        device_ctx = ModbusDeviceContext(
            hr=self._datablock,
            ir=self._ir_block,
        )
        device_ctx.simdevice.action = self._on_runtime_access
        logger.info("Runtime action enabled: %s", bool(device_ctx.simdevice.action))
        server_ctx = ModbusServerContext(
            devices={self.unit_id: device_ctx},
            single=False,
        )

        identity = ModbusDeviceIdentification()
        identity.VendorName = "SiteSee2 Sensor Simulator V5"
        identity.ProductCode = "SIM-SENSOR-5"
        identity.VendorUrl = "http://sitesee2.local"
        identity.ProductName = "Dummy Sensor Simulator V5"
        identity.ModelName = "SIM-SENSOR-5"
        identity.MajorMinorRevision = "5.0.0"

        self._update_task = asyncio.create_task(self._update_loop(), name="sensor-update")

        self._server = IPTrackingModbusTcpServer(
            context=server_ctx,
            identity=identity,
            address=(self.host, self.port),
            trace_connect=self._trace_connect,
            trace_pdu=self._trace_pdu,
            on_client_event=self._on_client_event,
        )

        logger.info(
            "Sensor simulator V5 listening on %s:%d  unit_id=%d  tags=%d  update_interval=%.0f ms  seed=%d",
            self.host,
            self.port,
            self.unit_id,
            SENSOR_COUNT,
            self._update_interval * 1_000,
            self._seed,
        )
        self._emit_connected_ips()

        await self._server.serve_forever()

    async def stop(self) -> None:
        self._running = False

        if self._update_task is not None and not self._update_task.done():
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass

        if self._server is not None:
            try:
                await self._server.shutdown()
            except Exception:
                logger.debug("Server shutdown raised", exc_info=True)
            self._server = None

        logger.info(
            "Simulator stopped - requests=%d  connections=%d  errors=%d",
            self.stats.request_count,
            self.stats.connection_count,
            self.stats.error_count,
        )

    def _trace_connect(self, connected: bool) -> None:
        if connected:
            self.stats.connection_count += 1
            logger.info("Client connected event (total connections=%d)", self.stats.connection_count)
        else:
            logger.info("Client disconnected event")

    def _trace_pdu(self, sending: bool, pdu: object) -> object:
        if not sending:
            self.stats.request_count += 1
            fc = getattr(pdu, "function_code", None)
            logger.debug("Request PDU  fc=0x%02X", fc if fc is not None else 0)
        return pdu

    def _on_client_event(self, ip: str, connected: bool) -> None:
        if connected:
            self._ip_connection_counts[ip] = self._ip_connection_counts.get(ip, 0) + 1
            logger.info("Client connected from %s", ip)
        else:
            current = self._ip_connection_counts.get(ip, 0)
            if current <= 1:
                self._ip_connection_counts.pop(ip, None)
            else:
                self._ip_connection_counts[ip] = current - 1
            logger.info("Client disconnected from %s", ip)

        self._emit_connected_ips()

    def _emit_connected_ips(self) -> None:
        active_ips = sorted(self._ip_connection_counts.keys())
        rendered = ",".join(active_ips) if active_ips else "none"
        logger.info("%s%s", CLIENT_IPS_TOKEN, rendered)

    def _pack_registers(self, values: Dict[str, int]) -> List[int]:
        regs: List[int] = [0] * TOTAL_REGISTERS
        for name, meta in REGISTER_MAP.items():
            regs[meta["address"]] = int(values[name])
        return regs

    def _format_values_line(self, values: Dict[str, int]) -> str:
        rendered = [f"{name}={values[name]}" for name in REGISTER_MAP.keys()]
        return " | ".join(rendered)

    async def _update_loop(self) -> None:
        while self._running:
            try:
                values = self._generator.compute_values(time.time())
                if self._show_values:
                    now_monotonic = time.monotonic()
                    if now_monotonic - self._last_display_ts >= self._display_interval:
                        logger.info("Simulated values: %s", self._format_values_line(values))
                        self._last_display_ts = now_monotonic
            except Exception:
                self.stats.error_count += 1
                logger.exception("Error in update loop")
            await asyncio.sleep(self._update_interval)


def _configure_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Modbus TCP 500-tag dummy sensor simulator V5 for SiteSee2 testing",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument(
        "--host",
        default=MeterSimulator.DEFAULT_HOST,
        metavar="ADDR",
        help="Bind address (0.0.0.0 listens on all interfaces for external clients)",
    )
    p.add_argument(
        "--port",
        default=MeterSimulator.DEFAULT_PORT,
        type=int,
        metavar="N",
        help="TCP port (ports <= 1023 require elevated privileges)",
    )
    p.add_argument(
        "--unit-id",
        default=MeterSimulator.DEFAULT_UNIT_ID,
        type=int,
        dest="unit_id",
        metavar="N",
        help="Modbus unit / slave ID (1-247)",
    )
    p.add_argument(
        "--seed",
        default=MeterSimulator.DEFAULT_SEED,
        type=int,
        metavar="N",
        help="Waveform phase seed (0-359); same seed -> same waveform on restart",
    )
    p.add_argument(
        "--interval",
        default=MeterSimulator.DEFAULT_UPDATE_INTERVAL_MS,
        type=int,
        dest="interval",
        metavar="MS",
        help="Register update interval in milliseconds",
    )
    p.add_argument(
        "--hide-values",
        action="store_true",
        help="Disable periodic logging of simulated parameter values",
    )
    p.add_argument(
        "--display-interval",
        default=MeterSimulator.DEFAULT_DISPLAY_INTERVAL_S,
        type=float,
        metavar="SEC",
        help="How often to print simulated values in seconds",
    )
    p.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable DEBUG-level logging",
    )
    return p


async def _async_main(args: argparse.Namespace) -> None:
    _configure_logging(args.verbose)
    simulator = MeterSimulator(
        host=args.host,
        port=args.port,
        unit_id=args.unit_id,
        seed=args.seed,
        update_interval_ms=args.interval,
        show_values=not args.hide_values,
        display_interval_s=args.display_interval,
    )

    loop = asyncio.get_running_loop()

    def _shutdown() -> None:
        logger.info("Shutdown signal received - stopping ...")
        asyncio.ensure_future(simulator.stop())

    if sys.platform != "win32":
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, _shutdown)
    else:
        signal.signal(signal.SIGTERM, lambda *_: loop.call_soon_threadsafe(_shutdown))

    await simulator.start()


def main() -> None:
    args = build_arg_parser().parse_args()
    try:
        asyncio.run(_async_main(args))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
