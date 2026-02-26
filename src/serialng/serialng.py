from typing import Callable
import time
import serial


class Serial:
    def __init__(
        self,
        device: str,
        baudrate: int = 115200,
        callback: Callable[[bytes], None] | None = None
    ):
        """
        device(str):     COMx or /dev/ttyY
        baudrate(int):   connection speed
        """
        self._device = device
        self._ser = serial.Serial(device, baudrate, timeout=0.1)
        self._opened_on_enter: bool = False
        self._callback: Callable[[bytes], None] | None = callback

    def __repr__(self) -> str:
        return f'<Serial "{self._device}">'

    def __del__(self):
        self._ser.close()

    def __enter__(self):
        if not self._ser.is_open:
            self._opened_on_enter = True
            self._ser.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._opened_on_enter:
            self._opened_on_enter = False
            self.close()

    def close(self):
        self._ser.close()

    def read(
            self,
            size=1,
    ) -> bytes:
        """
        read "size" characters from serial

        returns immediately in case no data is in the queue

        size(int):           number of characters to read at once
        """
        data = bytes()
        if self._ser.in_waiting > 0:
            # read whatever is smaller: in_waiting or size
            data = self._ser.read(
                self._ser.in_waiting if self._ser.in_waiting < size else size)
        if self._callback is not None:
            self._callback(data)
        return data

    def read_available(self) -> bytes:
        """read available data from serial"""
        return self.read(size=self._ser.in_waiting)

    def read_until(
            self,
            until: bytes = b'\n',
            timeout: float | None = None,
        ) -> bytes:
        """
        read from serial until a certain string appears

        until (bytes):       read until "until" appears
        timeout(None,float): abort after "timeout" seconds, infinite if None

        returns(bytes):      read data
        """
        ts_begin = time.time()
        data = b''
        while timeout is None or (time.time() - ts_begin) < timeout:
            new_bytes = b''
            for _ in range(self._ser.in_waiting):
                new_byte = self._ser.read(1)
                new_bytes += new_byte
                data += new_byte
                if data.endswith(until):
                    if self._callback is not None:
                        self._callback(new_bytes)
                    return data
            if self._callback is not None:
                self._callback(new_bytes)
        return data

    def write(self, data: bytes) -> int:
        """
        write data to the interface

        data(bytes):    data written to the interface

        returns(int):   number of written bytes
        """
        return self._ser.write(data)
