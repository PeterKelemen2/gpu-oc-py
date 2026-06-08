"""Inter-process communication layer for GPU OC service.

Provides a simple JSON-based RPC protocol over Unix socket for GUI ↔ service communication.
Server runs in the systemd service (app.py).
Client used by GUI to query status and control settings.
"""

import json
import socket
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


IPC_SOCKET_PATH = Path("/tmp/gpu-oc.sock")
IPC_TIMEOUT = 2.0  # seconds


@dataclass
class IPCMessage:
    """RPC message format: {"method": "...", "params": {...}, "id": 123}"""
    method: str
    params: dict[str, Any] = None
    message_id: int = 0

    def to_json(self) -> str:
        return json.dumps({
            "method": self.method,
            "params": self.params or {},
            "id": self.message_id,
        })

    @staticmethod
    def from_json(data: str) -> "IPCMessage":
        obj = json.loads(data)
        return IPCMessage(
            method=obj.get("method", ""),
            params=obj.get("params", {}),
            message_id=obj.get("id", 0),
        )


@dataclass
class IPCResponse:
    """Response format: {"result": ..., "error": null, "id": 123}"""
    result: Any = None
    error: str = None
    message_id: int = 0

    def to_json(self) -> str:
        return json.dumps({
            "result": self.result,
            "error": self.error,
            "id": self.message_id,
        })

    @staticmethod
    def from_json(data: str) -> "IPCResponse":
        obj = json.loads(data)
        return IPCResponse(
            result=obj.get("result"),
            error=obj.get("error"),
            message_id=obj.get("id", 0),
        )


class IPCServer:
    """RPC server listening on Unix socket for IPC requests."""

    def __init__(self):
        self._socket = None
        self._running = False
        self._handlers: dict[str, Callable] = {}
        self._thread = None

    def register_handler(self, method: str, handler: Callable) -> None:
        """Register a handler for a method.
        
        Handler signature: handler(params: dict) -> Any
        Should raise Exception for errors.
        """
        self._handlers[method] = handler

    def start(self) -> None:
        """Start listening for IPC requests (blocking)."""
        self._running = True
        # Clean up old socket
        if IPC_SOCKET_PATH.exists():
            IPC_SOCKET_PATH.unlink()

        self._socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._socket.bind(str(IPC_SOCKET_PATH))
        self._socket.listen(1)
        self._socket.settimeout(1.0)  # For interrupt checking

        print(f"IPC server listening on {IPC_SOCKET_PATH}")

        try:
            while self._running:
                try:
                    client, _ = self._socket.accept()
                    self._handle_client(client)
                except socket.timeout:
                    continue
        finally:
            self.stop()

    def start_background(self) -> None:
        """Start IPC server in a background thread."""
        self._thread = threading.Thread(target=self.start, daemon=True)
        self._thread.start()
        print("IPC server starting in background thread")

    def stop(self) -> None:
        """Stop the IPC server."""
        self._running = False
        if self._socket:
            self._socket.close()
        if IPC_SOCKET_PATH.exists():
            IPC_SOCKET_PATH.unlink()
        print("IPC server stopped")

    def _handle_client(self, client: socket.socket) -> None:
        """Handle a single client connection."""
        try:
            client.settimeout(IPC_TIMEOUT)
            data = client.recv(4096).decode("utf-8")
            
            if not data:
                return

            try:
                msg = IPCMessage.from_json(data)
                print(f"IPC request: {msg.method}")
                handler = self._handlers.get(msg.method)
                
                if not handler:
                    response = IPCResponse(
                        error=f"Unknown method: {msg.method}",
                        message_id=msg.message_id,
                    )
                else:
                    try:
                        result = handler(msg.params)
                        print(f"IPC response: {msg.method} → {result}")
                        response = IPCResponse(
                            result=result,
                            message_id=msg.message_id,
                        )
                    except Exception as e:
                        print(f"IPC error: {msg.method} → {e}")
                        response = IPCResponse(
                            error=str(e),
                            message_id=msg.message_id,
                        )
            except json.JSONDecodeError as e:
                print(f"IPC JSON error: {e}")
                response = IPCResponse(error=f"Invalid JSON: {e}")

            client.sendall(response.to_json().encode("utf-8"))
        except socket.timeout:
            pass
        except Exception as e:
            print(f"IPC client error: {e}")
        finally:
            client.close()


class IPCClient:
    """RPC client for connecting to GPU OC service."""

    def __init__(self, socket_path: Path = IPC_SOCKET_PATH):
        self._socket_path = socket_path
        self._message_id = 0

    def call(self, method: str, params: dict = None) -> Any:
        """Call a remote method and return the result."""
        self._message_id += 1
        msg = IPCMessage(method=method, params=params or {}, message_id=self._message_id)

        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.settimeout(IPC_TIMEOUT)
            sock.connect(str(self._socket_path))
            sock.sendall(msg.to_json().encode("utf-8"))
            
            response_data = sock.recv(4096).decode("utf-8")
            sock.close()
            
            response = IPCResponse.from_json(response_data)
            
            if response.error:
                raise RuntimeError(response.error)
            
            return response.result
        except (FileNotFoundError, ConnectionRefusedError):
            raise RuntimeError("GPU OC service not running. Start with: sudo systemctl start gpu-oc")
        except socket.timeout:
            raise RuntimeError("IPC communication timeout")

    def get_status(self) -> dict:
        """Get current GPU status."""
        return self.call("get_status")

    def toggle_oc(self, enabled: bool) -> dict:
        """Enable/disable OC without restarting service."""
        return self.call("toggle_oc", {"enabled": enabled})

    def set_fan_curve(self, points: list[list[int]]) -> dict:
        """Set fan curve points."""
        return self.call("set_fan_curve", {"points": points})

    def get_config(self) -> dict:
        """Get current OC configuration."""
        return self.call("get_config")
