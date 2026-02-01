import platform
import psutil
import sys
import subprocess
from typing import Dict
import ctypes
from ctypes import wintypes

class SystemInfo:
    """System information collector"""
    
    @staticmethod
    def _get_cpu_name_windows() -> str:
        """Get CPU name from Windows Registry"""
        try:
            import winreg
            reg_path = r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:
                cpu_name = winreg.QueryValueEx(key, "ProcessorNameString")[0]
                return cpu_name.strip()
        except Exception:
            pass
        
        # Fallback to wmic
        try:
            result = subprocess.check_output(
                "wmic cpu get name",
                shell=True,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                text=True
            ).strip().split('\n')
            
            for line in result:
                line = line.strip()
                if line and line.lower() != "name":
                    return line
        except Exception:
            pass
        
        return None
    
    @staticmethod
    def get_os_info() -> Dict[str, str]:
        """Get operating system information"""
        return {
            "OS": platform.system(),
            "OS Version": platform.release(),
            "OS Build": platform.version(),
            "Platform": sys.platform,
        }
    
    @staticmethod
    def get_processor_info() -> Dict[str, str]:
        """Get processor information"""
        try:
            cpu_model = "Unknown"
            
            # Try Windows Registry first (most reliable)
            if sys.platform == "win32":
                cpu_model = SystemInfo._get_cpu_name_windows()
            
            # Fallback to platform.processor()
            if not cpu_model:
                cpu_model = platform.processor()
                if not cpu_model or cpu_model == "":
                    cpu_model = "Unknown"
            
            return {
                "Model": cpu_model,
                "Architecture": f"{platform.machine()} ({platform.architecture()[0]})",
                "CPU Cores": str(psutil.cpu_count(logical=False)),
                "CPU Threads": str(psutil.cpu_count(logical=True)),
                "CPU Usage": f"{psutil.cpu_percent(interval=0.1)}%",
            }
        except Exception as e:
            return {
                "Model": f"Error: {str(e)}",
                "CPU Cores": str(psutil.cpu_count(logical=False)) if psutil.cpu_count(logical=False) else "Unknown",
                "CPU Threads": str(psutil.cpu_count(logical=True)) if psutil.cpu_count(logical=True) else "Unknown",
            }
    
    @staticmethod
    def get_memory_info() -> Dict[str, str]:
        """Get memory information"""
        memory = psutil.virtual_memory()
        total_gb = memory.total / (1024 ** 3)
        used_gb = memory.used / (1024 ** 3)
        available_gb = memory.available / (1024 ** 3)
        
        return {
            "Total Memory": f"{total_gb:.2f} GB",
            "Used Memory": f"{used_gb:.2f} GB",
            "Available Memory": f"{available_gb:.2f} GB",
            "Memory Usage": f"{memory.percent}%",
        }
    
    @staticmethod
    def get_disk_info() -> Dict[str, str]:
        """Get disk information for main drive"""
        try:
            disk = psutil.disk_usage('/')
            total_gb = disk.total / (1024 ** 3)
            used_gb = disk.used / (1024 ** 3)
            free_gb = disk.free / (1024 ** 3)
            
            return {
                "Disk Total": f"{total_gb:.2f} GB",
                "Disk Used": f"{used_gb:.2f} GB",
                "Disk Free": f"{free_gb:.2f} GB",
                "Disk Usage": f"{disk.percent}%",
            }
        except Exception as e:
            return {
                "Disk Info": f"Error: {str(e)}"
            }

    @staticmethod
    def get_monitors_info() -> Dict[str, str]:
        """Get connected monitors information.

        On Windows uses Win32 APIs (ctypes). On other platforms falls back to
        tkinter to report primary screen resolution.
        """
        monitors = []
        try:
            if sys.platform == "win32":
                user32 = ctypes.windll.user32

                class RECT(ctypes.Structure):
                    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                                ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

                class MONITORINFOEXW(ctypes.Structure):
                    _fields_ = [("cbSize", wintypes.DWORD),
                                ("rcMonitor", RECT),
                                ("rcWork", RECT),
                                ("dwFlags", wintypes.DWORD),
                                ("szDevice", ctypes.c_wchar * 32)]

                MonitorEnumProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HMONITOR, wintypes.HDC,
                                                     ctypes.POINTER(RECT), wintypes.LPARAM)

                def _callback(hMonitor, hdcMonitor, lprcMonitor, dwData):
                    mi = MONITORINFOEXW()
                    mi.cbSize = ctypes.sizeof(MONITORINFOEXW)
                    res = user32.GetMonitorInfoW(hMonitor, ctypes.byref(mi))
                    if res:
                        left, top = mi.rcMonitor.left, mi.rcMonitor.top
                        right, bottom = mi.rcMonitor.right, mi.rcMonitor.bottom
                        width = right - left
                        height = bottom - top
                        device = mi.szDevice
                        primary = bool(mi.dwFlags & 1)
                        monitors.append({
                            "Device": device,
                            "Resolution": f"{width}x{height}",
                            "Primary": "Yes" if primary else "No"
                        })
                    return True

                user32.EnumDisplayMonitors(0, 0, MonitorEnumProc(_callback), 0)
            else:
                # Fallback: report primary display via tkinter (common on Unix/mac)
                try:
                    import tkinter as tk
                    root = tk.Tk()
                    root.withdraw()
                    w = root.winfo_screenwidth()
                    h = root.winfo_screenheight()
                    root.destroy()
                    monitors.append({
                        "Device": "Primary",
                        "Resolution": f"{w}x{h}",
                        "Primary": "Yes"
                    })
                except Exception:
                    pass

        except Exception:
            monitors = []

        info = {}
        info["Monitor Count"] = str(len(monitors))
        for i, m in enumerate(monitors, start=1):
            info[f"Monitor {i}"] = f"{m.get('Device','')}: {m.get('Resolution','')} (Primary: {m.get('Primary','No')})"

        if not monitors:
            info["Monitor Info"] = "Unavailable"

        return info
    
    @staticmethod
    def get_python_info() -> Dict[str, str]:
        """Get Python information"""
        return {
            "Python Version": platform.python_version(),
            "Python Compiler": platform.python_compiler(),
            "Python Implementation": platform.python_implementation(),
        }
    
    @staticmethod
    def get_all_info() -> Dict[str, Dict[str, str]]:
        """Get all system information"""
        return {
            "Operating System": SystemInfo.get_os_info(),
            "Processor": SystemInfo.get_processor_info(),
            "Memory": SystemInfo.get_memory_info(),
            "Disk": SystemInfo.get_disk_info(),
            "Python": SystemInfo.get_python_info(),
            "Monitors": SystemInfo.get_monitors_info(),
        }
    
    @staticmethod
    def format_info_display() -> str:
        """Format all info for display"""
        all_info = SystemInfo.get_all_info()
        display_text = ""
        
        for section, info_dict in all_info.items():
            display_text += f"\n{section}:\n"
            display_text += "=" * 50 + "\n"
            for key, value in info_dict.items():
                # Improve alignment and readability
                display_text += f"  {key:<20} : {value}\n"
            display_text += "\n"
        
        return display_text
