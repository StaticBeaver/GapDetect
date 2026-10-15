"""Raw communication with USB barcode/label printers directly via
CreateFile/ReadFile/WriteFile through the Windows USBPRINT device interface
(GUID_DEVINTERFACE_USBPRINT).

This never touches the Windows print spooler - no driver changes are needed
and your existing printer queue is left intact. Microsoft's generic USB
Printer Class driver (usbprint.sys) automatically exposes this interface for
every USB printer; we simply connect to it.

The device is opened with FILE_FLAG_OVERLAPPED and all reads/writes are done
asynchronously using the OVERLAPPED structure. The reason: a synchronous
(blocking) ReadFile has no timeout, so if the printer never answers the call
hangs forever - and while such a call is pending, CloseHandle deadlocks too.
In overlapped mode, a timed-out operation can be cleanly cancelled with
CancelIoEx and the handle closed safely.
"""
import ctypes
from ctypes import wintypes

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
setupapi = ctypes.WinDLL("setupapi", use_last_error=True)
ole32 = ctypes.WinDLL("ole32", use_last_error=True)

GUID_DEVINTERFACE_USBPRINT = "{28D78FAD-5A12-11D1-AE5B-0000F803A8C2}"

DIGCF_PRESENT = 0x02
DIGCF_DEVICEINTERFACE = 0x10
GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002
OPEN_EXISTING = 3
FILE_FLAG_OVERLAPPED = 0x40000000
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value
ERROR_IO_PENDING = 997
WAIT_TIMEOUT = 0x102
WAIT_OBJECT_0 = 0x0


class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", ctypes.c_ubyte * 8),
    ]


class SP_DEVICE_INTERFACE_DATA(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("InterfaceClassGuid", GUID),
        ("Flags", wintypes.DWORD),
        ("Reserved", ctypes.POINTER(ctypes.c_ulong)),
    ]


class SP_DEVINFO_DATA(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("ClassGuid", GUID),
        ("DevInst", wintypes.DWORD),
        ("Reserved", ctypes.c_void_p),
    ]


class OVERLAPPED(ctypes.Structure):
    _fields_ = [
        ("Internal", ctypes.c_void_p),
        ("InternalHigh", ctypes.c_void_p),
        ("Offset", wintypes.DWORD),
        ("OffsetHigh", wintypes.DWORD),
        ("hEvent", wintypes.HANDLE),
    ]


ole32.CLSIDFromString.argtypes = [wintypes.LPCWSTR, ctypes.POINTER(GUID)]

setupapi.SetupDiGetClassDevsW.restype = wintypes.HANDLE
setupapi.SetupDiGetClassDevsW.argtypes = [
    ctypes.POINTER(GUID),
    wintypes.LPCWSTR,
    wintypes.HWND,
    wintypes.DWORD,
]

setupapi.SetupDiEnumDeviceInterfaces.restype = wintypes.BOOL
setupapi.SetupDiEnumDeviceInterfaces.argtypes = [
    wintypes.HANDLE,
    ctypes.c_void_p,
    ctypes.POINTER(GUID),
    wintypes.DWORD,
    ctypes.POINTER(SP_DEVICE_INTERFACE_DATA),
]

setupapi.SetupDiGetDeviceInterfaceDetailW.restype = wintypes.BOOL
setupapi.SetupDiGetDeviceInterfaceDetailW.argtypes = [
    wintypes.HANDLE,
    ctypes.POINTER(SP_DEVICE_INTERFACE_DATA),
    ctypes.c_void_p,
    wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD),
    ctypes.c_void_p,
]

setupapi.SetupDiGetDeviceRegistryPropertyW.restype = wintypes.BOOL
setupapi.SetupDiGetDeviceRegistryPropertyW.argtypes = [
    wintypes.HANDLE,
    ctypes.c_void_p,
    wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD),
    ctypes.c_void_p,
    wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD),
]

setupapi.SetupDiDestroyDeviceInfoList.argtypes = [wintypes.HANDLE]

kernel32.CreateFileW.restype = wintypes.HANDLE
kernel32.CreateFileW.argtypes = [
    wintypes.LPCWSTR,
    wintypes.DWORD,
    wintypes.DWORD,
    ctypes.c_void_p,
    wintypes.DWORD,
    wintypes.DWORD,
    wintypes.HANDLE,
]

kernel32.WriteFile.restype = wintypes.BOOL
kernel32.WriteFile.argtypes = [
    wintypes.HANDLE,
    ctypes.c_void_p,
    wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD),
    ctypes.POINTER(OVERLAPPED),
]

kernel32.ReadFile.restype = wintypes.BOOL
kernel32.ReadFile.argtypes = [
    wintypes.HANDLE,
    ctypes.c_void_p,
    wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD),
    ctypes.POINTER(OVERLAPPED),
]

kernel32.CreateEventW.restype = wintypes.HANDLE
kernel32.CreateEventW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.BOOL, wintypes.LPCWSTR]

kernel32.WaitForSingleObject.restype = wintypes.DWORD
kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]

kernel32.GetOverlappedResult.restype = wintypes.BOOL
kernel32.GetOverlappedResult.argtypes = [
    wintypes.HANDLE,
    ctypes.POINTER(OVERLAPPED),
    ctypes.POINTER(wintypes.DWORD),
    wintypes.BOOL,
]

kernel32.CancelIoEx.restype = wintypes.BOOL
kernel32.CancelIoEx.argtypes = [wintypes.HANDLE, ctypes.POINTER(OVERLAPPED)]

kernel32.CloseHandle.argtypes = [wintypes.HANDLE]


def _guid(text: str) -> GUID:
    g = GUID()
    hr = ole32.CLSIDFromString(text, ctypes.byref(g))
    if hr != 0:
        raise OSError(f"CLSIDFromString failed: 0x{hr & 0xFFFFFFFF:08X}")
    return g


def list_usbprint_device_paths():
    """Returns the Win32 paths of all USBPRINT device interfaces present on the system."""
    guid = _guid(GUID_DEVINTERFACE_USBPRINT)
    hinfo = setupapi.SetupDiGetClassDevsW(
        ctypes.byref(guid), None, None, DIGCF_PRESENT | DIGCF_DEVICEINTERFACE
    )
    if hinfo == INVALID_HANDLE_VALUE or not hinfo:
        err = ctypes.get_last_error()
        raise OSError(f"SetupDiGetClassDevs failed (WinError {err}): {ctypes.FormatError(err)}")

    paths = []
    try:
        index = 0
        while True:
            did = SP_DEVICE_INTERFACE_DATA()
            did.cbSize = ctypes.sizeof(SP_DEVICE_INTERFACE_DATA)
            ok = setupapi.SetupDiEnumDeviceInterfaces(hinfo, None, ctypes.byref(guid), index, ctypes.byref(did))
            if not ok:
                break  # ERROR_NO_MORE_ITEMS is the expected end condition

            required = wintypes.DWORD(0)
            setupapi.SetupDiGetDeviceInterfaceDetailW(hinfo, ctypes.byref(did), None, 0, ctypes.byref(required), None)

            buf = ctypes.create_string_buffer(required.value)
            cb_size_value = 8 if ctypes.sizeof(ctypes.c_void_p) == 8 else 6
            ctypes.memmove(buf, ctypes.byref(wintypes.DWORD(cb_size_value)), 4)

            ok = setupapi.SetupDiGetDeviceInterfaceDetailW(
                hinfo, ctypes.byref(did), buf, required, None, None
            )
            if ok:
                device_path = ctypes.wstring_at(ctypes.addressof(buf) + 4)
                paths.append(device_path)
            index += 1
    finally:
        setupapi.SetupDiDestroyDeviceInfoList(hinfo)
    return paths


def list_usbprint_devices_with_names():
    """Returns the paths and names of all USBPRINT device interfaces present on the system.
    Returns: [(device_path, friendly_name), ...]"""
    guid = _guid(GUID_DEVINTERFACE_USBPRINT)
    hinfo = setupapi.SetupDiGetClassDevsW(
        ctypes.byref(guid), None, None, DIGCF_PRESENT | DIGCF_DEVICEINTERFACE
    )
    if hinfo == INVALID_HANDLE_VALUE or not hinfo:
        return []

    devices = []
    try:
        index = 0
        while True:
            did = SP_DEVICE_INTERFACE_DATA()
            did.cbSize = ctypes.sizeof(SP_DEVICE_INTERFACE_DATA)
            ok = setupapi.SetupDiEnumDeviceInterfaces(hinfo, None, ctypes.byref(guid), index, ctypes.byref(did))
            if not ok:
                break

            required = wintypes.DWORD(0)
            setupapi.SetupDiGetDeviceInterfaceDetailW(hinfo, ctypes.byref(did), None, 0, ctypes.byref(required), None)

            buf = ctypes.create_string_buffer(required.value)
            cb_size_value = 8 if ctypes.sizeof(ctypes.c_void_p) == 8 else 6
            ctypes.memmove(buf, ctypes.byref(wintypes.DWORD(cb_size_value)), 4)

            devinfo = SP_DEVINFO_DATA()
            devinfo.cbSize = ctypes.sizeof(SP_DEVINFO_DATA)

            ok = setupapi.SetupDiGetDeviceInterfaceDetailW(
                hinfo, ctypes.byref(did), buf, required, None, ctypes.byref(devinfo)
            )
            if ok:
                device_path = ctypes.wstring_at(ctypes.addressof(buf) + 4)
                
                prop_buf = ctypes.create_string_buffer(1024)
                prop_req = wintypes.DWORD(0)
                
                name = "Unknown USB Printer"
                # SPDRP_FRIENDLYNAME = 12
                if setupapi.SetupDiGetDeviceRegistryPropertyW(hinfo, ctypes.byref(devinfo), 12, None, prop_buf, 1024, ctypes.byref(prop_req)):
                    name = ctypes.wstring_at(prop_buf)
                else:
                    # SPDRP_DEVICEDESC = 0
                    if setupapi.SetupDiGetDeviceRegistryPropertyW(hinfo, ctypes.byref(devinfo), 0, None, prop_buf, 1024, ctypes.byref(prop_req)):
                        name = ctypes.wstring_at(prop_buf)
                        
                devices.append((device_path, name))
            index += 1
    finally:
        setupapi.SetupDiDestroyDeviceInfoList(hinfo)
    return devices


class RawUsbPrinter:
    def __init__(self, device_path: str):
        self.device_path = device_path
        self._handle = None

    def open(self):
        h = kernel32.CreateFileW(
            self.device_path,
            GENERIC_READ | GENERIC_WRITE,
            FILE_SHARE_READ | FILE_SHARE_WRITE,
            None,
            OPEN_EXISTING,
            FILE_FLAG_OVERLAPPED,
            None,
        )
        if h == INVALID_HANDLE_VALUE or not h:
            err = ctypes.get_last_error()
            raise OSError(f"CreateFile failed (WinError {err}): {ctypes.FormatError(err)}")
        self._handle = h

    def close(self):
        if self._handle:
            kernel32.CloseHandle(self._handle)
            self._handle = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def _overlapped_io(self, io_func, buf, size, timeout: float):
        """Runs WriteFile/ReadFile in overlapped mode, waits up to `timeout`
        seconds, and cancels with CancelIoEx if it doesn't complete.

        Returns: (byte_count, error_or_None)
        """
        evt = kernel32.CreateEventW(None, True, False, None)
        if not evt:
            err = ctypes.get_last_error()
            raise OSError(f"CreateEvent failed (WinError {err}): {ctypes.FormatError(err)}")

        ov = OVERLAPPED()
        ov.hEvent = evt
        try:
            n = wintypes.DWORD(0)
            ok = io_func(self._handle, buf, size, ctypes.byref(n), ctypes.byref(ov))
            if not ok:
                err = ctypes.get_last_error()
                if err != ERROR_IO_PENDING:
                    return 0, OSError(f"Could not start I/O (WinError {err}): {ctypes.FormatError(err)}")

                wait_result = kernel32.WaitForSingleObject(evt, int(timeout * 1000))
                if wait_result == WAIT_TIMEOUT:
                    kernel32.CancelIoEx(self._handle, ctypes.byref(ov))
                    # Wait for the cancellation to complete (so the handle can be closed safely)
                    kernel32.GetOverlappedResult(self._handle, ctypes.byref(ov), ctypes.byref(n), True)
                    return 0, TimeoutError(f"Did not complete within {timeout} seconds (cancelled).")
                if wait_result != WAIT_OBJECT_0:
                    return 0, OSError(f"WaitForSingleObject unexpected result: {wait_result}")

                result_ok = kernel32.GetOverlappedResult(self._handle, ctypes.byref(ov), ctypes.byref(n), False)
                if not result_ok:
                    err = ctypes.get_last_error()
                    return 0, OSError(f"GetOverlappedResult failed (WinError {err}): {ctypes.FormatError(err)}")
            return n.value, None
        finally:
            kernel32.CloseHandle(evt)

    def write(self, data: bytes, timeout: float = 3.0):
        """Returns (bytes_written, error_or_None)."""
        if self._handle is None:
            raise RuntimeError("Device is not open.")
        buf = ctypes.create_string_buffer(data, len(data))
        return self._overlapped_io(kernel32.WriteFile, buf, len(data), timeout)

    def read(self, size: int = 512, timeout: float = 3.0):
        """Returns (data, error_or_None)."""
        if self._handle is None:
            raise RuntimeError("Device is not open.")
        buf = ctypes.create_string_buffer(size)
        n, err = self._overlapped_io(kernel32.ReadFile, buf, size, timeout)
        if err is not None:
            return b"", err
        return buf.raw[:n], None
