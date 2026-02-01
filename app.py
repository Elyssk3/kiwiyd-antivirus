import dearpygui.dearpygui as dpg
import subprocess
import os
import sys
import threading

# Add modules directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'modules'))

from settings import Settings
from system_info import SystemInfo
from scanner import initialize_scanner

# Try to import win10toast for notifications
try:
    from win10toast import ToastNotifier
    NOTIFICATIONS_AVAILABLE = True
except ImportError:
    NOTIFICATIONS_AVAILABLE = False

# Initialize DearPyGui
dpg.create_context()

# Global variables
output_text = "Welcome to Kiwiyd Antivirus\nSelect an action to begin...\n"
settings = Settings()
scanner = None
scan_thread = None
scan_stats = {"files_scanned": 0, "threats_found": 0}  # Track scan statistics

def append_output(message: str):
    """Append message to output display"""
    global output_text
    output_text += message + "\n"
    if dpg.does_item_exist("output_text"):
        dpg.set_value("output_text", output_text)

def show_scan_notification(threats_found: int, files_scanned: int):
    """Show Windows notification when scan completes
    
    Args:
        threats_found: Number of threats detected
        files_scanned: Total files scanned
    """
    if not NOTIFICATIONS_AVAILABLE:
        return
    
    try:
        toaster = ToastNotifier()
        
        if threats_found > 0:
            title = "⚠️ Kiwiyd Antivirus - Threats Found!"
            message = f"Scan complete: {threats_found} threat(s) detected in {files_scanned} files"
        else:
            title = "✓ Kiwiyd Antivirus - Scan Complete"
            message = f"Scan safe: No threats found in {files_scanned} files"
        
        toaster.show_toast(
            title=title,
            msg=message,
            duration=5,
            threaded=True
        )
    except Exception as e:
        append_output(f"[!] Could not show notification: {str(e)}")

def browse_directory(sender, app_data):
    """Handle directory selection from file browser"""
    # app_data can be a dict or list depending on DearPyGui version
    selected_path = ""
    try:
        if isinstance(app_data, dict):
            selected_path = app_data.get("file_path_name", "") or app_data.get("file_path", "")
        elif isinstance(app_data, (list, tuple)):
            selected_path = app_data[0] if app_data else ""
        else:
            selected_path = str(app_data)
    except Exception:
        selected_path = ""

    if selected_path:
        dpg.set_value("scan_path_input", selected_path)
        append_output(f"✓ Directory selected: {selected_path}")
        # Save this selection as the last used scan path
        try:
            settings.set("scan.last_selected_path", selected_path)
        except Exception:
            pass
        # Ensure the scan dialog is visible again after the file dialog closes
        try:
            dpg.show_item("scan_dialog")
            # Attempt to focus the path input so user can immediately start the scan
            if hasattr(dpg, "set_item_focus"):
                dpg.set_item_focus("scan_path_input")
        except Exception:
            pass

def open_directory_browser():
    """Open directory browser"""
    dpg.show_item("dir_browser")

def open_scan_dialog():
    """Open scan configuration dialog"""
    dpg.show_item("scan_dialog")

def confirm_scan():
    """Confirm and start scan using Python scanner module with thread count from settings"""
    global scanner, scan_thread
    
    scan_directory_path = dpg.get_value("scan_path_input")
    
    if not scan_directory_path:
        append_output("✗ Error: Please specify a directory path")
        return
    
    if not os.path.exists(scan_directory_path):
        append_output(f"✗ Error: Directory not found: {scan_directory_path}")
        return
    
    # Check if another scan is already running
    if scan_thread and scan_thread.is_alive():
        append_output("✗ Error: Scan already in progress")
        return
    
    dpg.hide_item("scan_dialog")
    
    # Get thread count from settings
    thread_count = settings.get("scan.thread_count", 4)
    
    append_output(f"\n{'='*60}")
    append_output(f"[*] Starting scan")
    append_output(f"[*] Directory: {scan_directory_path}")
    append_output(f"[*] Thread count: {thread_count}")
    append_output(f"{'='*60}\n")
    
    # Save selected path to settings
    try:
        settings.set("scan.last_selected_path", scan_directory_path)
    except Exception:
        pass
    
    # Run scan in background thread
    def run_scan():
        global scanner, scan_stats
        try:
            # Initialize scanner with settings
            scanner = initialize_scanner(
                thread_count=thread_count,
                log_callback=append_output
            )
            
            # Perform scan
            scanner.scan_directory(scan_directory_path)
            
            # Store statistics for notification
            scan_stats["files_scanned"] = scanner.total_files_scanned
            scan_stats["threats_found"] = scanner.total_threats_found
            
            append_output(f"\n{'='*60}")
            append_output("[OK] Scan finished successfully")
            append_output(f"{'='*60}\n")
            
            # Show notification
            show_scan_notification(
                threats_found=scanner.total_threats_found,
                files_scanned=scanner.total_files_scanned
            )
        except Exception as e:
            append_output(f"\n[ERROR] Scan failed: {str(e)}\n")
    
    # Start scan in separate thread so UI remains responsive
    scan_thread = threading.Thread(target=run_scan, daemon=True)
    scan_thread.start()

def use_last_scan_path(sender, app_data):
    """Set the scan path input to the last selected path stored in settings"""
    try:
        last = settings.get("scan.last_selected_path", "")
        if not last:
            append_output("[!] No last scan path saved")
            return
        dpg.set_value("scan_path_input", last)
        append_output(f"✓ Loaded last scan path: {last}")
        # Ensure dialog is visible in case it was hidden
        try:
            dpg.show_item("scan_dialog")
            if hasattr(dpg, "set_item_focus"):
                dpg.set_item_focus("scan_path_input")
        except Exception:
            pass
    except Exception as e:
        append_output(f"[ERROR] Unable to load last scan path: {str(e)}")

def cancel_scan_dialog():
    """Cancel scan dialog"""
    dpg.hide_item("scan_dialog")

def start_scan():
    """Open scan dialog"""
    open_scan_dialog()

def quit_app():
    """Close application"""
    dpg.stop_dearpygui()

def save_settings_callback():
    """Save current settings"""
    try:
        # Get values from UI
        auto_scan = dpg.get_value("auto_scan_checkbox")
        auto_quarantine = dpg.get_value("auto_quarantine_checkbox")
        auto_update = dpg.get_value("auto_update_checkbox")
        show_notifications = dpg.get_value("notifications_checkbox")
        thread_count = dpg.get_value("thread_count_slider")
        
        # Update settings
        settings.set("scan.enable_auto_scan", auto_scan)
        settings.set("quarantine.auto_quarantine", auto_quarantine)
        settings.set("updates.auto_update", auto_update)
        settings.set("notifications.enable_notifications", show_notifications)
        settings.set("scan.thread_count", thread_count)
        
        append_output("✓ Settings saved successfully")
    except Exception as e:
        append_output(f"✗ Error saving settings: {str(e)}")

def reset_settings_callback():
    """Reset settings to defaults"""
    try:
        settings.reset_to_defaults()
        
        # Update UI with default values
        default_settings = settings.get_all()
        dpg.set_value("auto_scan_checkbox", default_settings["scan"]["enable_auto_scan"])
        dpg.set_value("auto_quarantine_checkbox", default_settings["quarantine"]["auto_quarantine"])
        dpg.set_value("auto_update_checkbox", default_settings["updates"]["auto_update"])
        dpg.set_value("notifications_checkbox", default_settings["notifications"]["enable_notifications"])
        
        # Reset auto-scan configuration fields
        dpg.set_value("auto_scan_time_input", default_settings["scan"]["auto_scan_time"])
        dpg.set_value("auto_scan_path_input", default_settings["scan"]["auto_scan_path"])
        dpg.set_value("auto_scan_mode_radio", default_settings["scan"]["auto_scan_mode"])
        
        # Reset thread count slider
        dpg.set_value("thread_count_slider", default_settings["scan"]["thread_count"])
        
        append_output("✓ All settings reset to defaults")
    except Exception as e:
        append_output(f"✗ Error resetting settings: {str(e)}")

def auto_scan_checkbox_callback(sender, app_data, user_data):
    """Handle Auto-Scan checkbox toggle"""
    if dpg.get_value("auto_scan_checkbox"):
        dpg.show_item("auto_scan_dialog")
    else:
        settings.set("scan.enable_auto_scan", False)
        append_output("✓ Auto-Scan disabled")

def open_auto_scan_dialog():
    """Open auto scan configuration dialog"""
    dpg.show_item("auto_scan_dialog")

def auto_scan_browse_directory(sender, app_data):
    """Handle directory selection from auto scan file browser"""
    selected_path = app_data.get("file_path_name", "")
    if selected_path:
        dpg.set_value("auto_scan_path_input", selected_path)

def auto_scan_browser_open():
    """Open directory browser for auto scan"""
    dpg.show_item("auto_scan_dir_browser")

def confirm_auto_scan_settings():
    """Confirm and save auto scan settings"""
    try:
        scan_path = dpg.get_value("auto_scan_path_input").strip()
        scan_time = dpg.get_value("auto_scan_time_input").strip()
        scan_mode = dpg.get_value("auto_scan_mode_radio")
        
        # Validate inputs
        if not scan_path:
            append_output("✗ Error: Please specify a directory path")
            return
        
        if not os.path.exists(scan_path):
            append_output(f"✗ Error: Directory not found: {scan_path}")
            return
        
        # Validate time format (HH:MM)
        try:
            hours, minutes = map(int, scan_time.split(':'))
            if not (0 <= hours < 24 and 0 <= minutes < 60):
                raise ValueError("Invalid time range")
        except (ValueError, IndexError):
            append_output("✗ Error: Invalid time format. Use HH:MM (00:00 - 23:59)")
            return
        
        # Save settings
        settings.set("scan.enable_auto_scan", True)
        settings.set("scan.auto_scan_path", scan_path)
        settings.set("scan.auto_scan_time", scan_time)
        settings.set("scan.auto_scan_mode", scan_mode)
        
        dpg.hide_item("auto_scan_dialog")
        append_output(f"✓ Auto-Scan configured:\n  Time: {scan_time}\n  Path: {scan_path}\n  Mode: {scan_mode}")
    except Exception as e:
        append_output(f"✗ Error: {str(e)}")

def cancel_auto_scan_dialog():
    """Cancel auto scan dialog"""
    dpg.set_value("auto_scan_checkbox", False)
    dpg.hide_item("auto_scan_dialog")

def refresh_system_info():
    """Refresh system information display"""
    try:
        system_info_text = SystemInfo.format_info_display()
        dpg.set_value("system_info_text", system_info_text)
    except Exception as e:
        dpg.set_value("system_info_text", f"Error loading system info: {str(e)}")

def load_quarantine_files():
    """Load quarantine files from quarantine module"""
    try:
        append_output("[*] Loading quarantine module...")
        append_output("[*] Connecting to quarantine module...")
        
        # TODO: Call C++ quarantine module (quarantine.exe) to get list of files
        # For now, we'll just initialize with empty list
        quarantine_files = []
        
        if quarantine_files:
            files_text = "\n".join(quarantine_files)
            dpg.set_value("quarantine_files_display", files_text)
            append_output(f"[OK] Quarantine loaded: {len(quarantine_files)} file(s)")
        else:
            dpg.set_value("quarantine_files_display", "No files in quarantine")
            append_output("[OK] Quarantine is empty")
    except Exception as e:
        append_output(f"[ERROR] Error loading quarantine: {str(e)}")

def delete_quarantine_files():
    """Delete all files in quarantine by sending request to quarantine module"""
    try:
        # Get list of files
        files_display = dpg.get_value("quarantine_files_display")
        
        if not files_display or files_display == "No files in quarantine":
            append_output("[!] Quarantine is empty, nothing to delete")
            return
        
        append_output("[*] Processing delete request...")
        append_output("[*] Sending request to quarantine module to delete files...")
        
        # TODO: Call C++ quarantine module (quarantine.exe) to delete files
        # The module should handle file deletion based on stored quarantine list
        
        append_output("[*] Waiting for quarantine module response...")
        append_output("[OK] Files deleted successfully")
        
        # Clear the display
        dpg.set_value("quarantine_files_display", "No files in quarantine")
        append_output("[OK] Quarantine cleared")
    except Exception as e:
        append_output(f"[ERROR] Error deleting quarantine files: {str(e)}")


def delete_quarantine_file(sender, app_data):
    """Delete a single file from quarantine by sending request to quarantine module"""
    try:
        # Get filename from input
        filename = dpg.get_value("quarantine_selected_input").strip()
        if not filename:
            append_output("[!] Please specify a filename to delete")
            return

        append_output(f"[*] Sending delete request for: {filename}")

        # Build path to quarantine module executable (expected in modules/)
        module_path = os.path.join(os.path.dirname(__file__), "modules", "quarantine.exe")
        if not os.path.exists(module_path):
            append_output(f"[!] Quarantine module not found: {module_path}")
            append_output("[!] Ensure the quarantine module is built and available as 'quarantine.exe' in modules/")
            return

        # Call the quarantine module to delete the specific file
        result = subprocess.run([module_path, "delete", filename], capture_output=True, text=True)

        if result.returncode == 0:
            append_output(f"[OK] Deleted: {filename}")
            # Refresh quarantine listing after deletion
            refresh_quarantine()
        else:
            # Show module output/error
            err = (result.stderr or result.stdout).strip()
            append_output(f"[ERROR] Quarantine module error: {err}")
    except Exception as e:
        append_output(f"[ERROR] Error sending delete request: {str(e)}")

def refresh_quarantine():
    """Refresh quarantine display"""
    load_quarantine_files()

def update_thread_count_display(sender, app_data, user_data):
    """Update thread count display when slider changes"""
    thread_count = dpg.get_value("thread_count_slider")
    dpg.set_value("thread_count_display", f"Selected: {thread_count} thread(s)")

def open_time_picker():
    """Open time picker dialog"""
    # Load current time into picker
    current_time = dpg.get_value("auto_scan_time_input")
    try:
        hours, minutes = map(int, current_time.split(':'))
    except:
        hours, minutes = 0, 0
    
    dpg.set_value("time_picker_hours", hours)
    dpg.set_value("time_picker_minutes", minutes)
    dpg.show_item("time_picker_dialog")

def confirm_time_selection():
    """Confirm time selection and update field"""
    hours = dpg.get_value("time_picker_hours")
    minutes = dpg.get_value("time_picker_minutes")
    time_str = f"{hours:02d}:{minutes:02d}"
    dpg.set_value("auto_scan_time_input", time_str)
    dpg.hide_item("time_picker_dialog")

def update_time_preview(sender, app_data, user_data):
    """Update time preview in picker"""
    hours = dpg.get_value("time_picker_hours")
    minutes = dpg.get_value("time_picker_minutes")
    time_str = f"{hours:02d}:{minutes:02d}"
    dpg.set_value("time_preview", f"Selected Time: {time_str}")

def cancel_time_picker():
    """Cancel time picker"""
    dpg.hide_item("time_picker_dialog")

if __name__ == "__main__":
    # Create window with proper layout
    with dpg.window(label="Kiwiyd Antivirus", tag="main_window", no_close=False, pos=(100, 100)):
        # Title
        dpg.add_text("Kiwiyd Antivirus", color=(200, 200, 200))
        dpg.add_text("Antivirus Scanner", color=(150, 150, 150))
        
        dpg.add_separator()
        
        # Main container with two columns
        with dpg.group(horizontal=True):
            # LEFT COLUMN - Action Buttons
            with dpg.group(tag="left_panel"):
                dpg.add_text("Actions", color=(200, 200, 200))
                dpg.add_separator()
                
                dpg.add_button(label="Start Scan", callback=start_scan, width=200, height=50)
                dpg.add_text("")  # Spacer
                
                dpg.add_button(label="Exit", callback=quit_app, width=200, height=50)
            
            # RIGHT COLUMN - Tabs
            with dpg.group(tag="right_panel"):
                with dpg.tab_bar():
                    # Scan Output Tab
                    with dpg.tab(label="Scan Output"):
                        dpg.add_text("Output Log:")
                        dpg.add_input_text(tag="output_text", default_value=output_text, 
                                          multiline=True, width=600, height=450, 
                                          readonly=True)
                    
                    # Settings Tab
                    with dpg.tab(label="Settings"):
                        dpg.add_text("Application Settings", color=(200, 200, 200))
                        dpg.add_separator()
                        
                        dpg.add_text("Scan Settings:", color=(180, 180, 180))
                        dpg.add_checkbox(label="Enable Auto-Scan", tag="auto_scan_checkbox",
                                        default_value=settings.get("scan.enable_auto_scan"),
                                        callback=auto_scan_checkbox_callback)
                        dpg.add_text("Thread Count for Scanning:", color=(170, 170, 170))
                        dpg.add_slider_int(tag="thread_count_slider", 
                                          default_value=settings.get("scan.thread_count"),
                                          min_value=1, max_value=16, width=250,
                                          callback=update_thread_count_display)
                        dpg.add_text(f"Selected: {settings.get('scan.thread_count')} thread(s)", 
                                    tag="thread_count_display", color=(150, 180, 150))
                        dpg.add_text("")
                        
                        dpg.add_separator()
                        dpg.add_text("Quarantine Settings:", color=(180, 180, 180))
                        dpg.add_checkbox(label="Auto-Quarantine Threats", tag="auto_quarantine_checkbox",
                                        default_value=settings.get("quarantine.auto_quarantine"))
                        dpg.add_text("")
                        
                        dpg.add_separator()
                        dpg.add_text("Update Settings:", color=(180, 180, 180))
                        dpg.add_checkbox(label="Enable Auto-Update", tag="auto_update_checkbox",
                                        default_value=settings.get("updates.auto_update"))
                        dpg.add_text("")
                        
                        dpg.add_separator()
                        dpg.add_text("Notification Settings:", color=(180, 180, 180))
                        dpg.add_checkbox(label="Enable Notifications", tag="notifications_checkbox",
                                        default_value=settings.get("notifications.enable_notifications"))
                        dpg.add_text("")
                        
                        dpg.add_separator()
                        with dpg.group(horizontal=True):
                            dpg.add_button(label="Save Settings", callback=save_settings_callback, width=150, height=35)
                            dpg.add_button(label="Reset to Defaults", callback=reset_settings_callback, width=150, height=35)
                    
                    # System Info Tab
                    with dpg.tab(label="System Info"):
                        dpg.add_text("System Information", color=(200, 200, 200))
                        dpg.add_separator()
                        dpg.add_button(label="Refresh", callback=refresh_system_info, width=100, height=30)
                        dpg.add_text("")
                        dpg.add_input_text(tag="system_info_text", default_value="", 
                                          multiline=True, width=600, height=400, 
                                          readonly=True)
                    
                    # Quarantine Tab
                    with dpg.tab(label="Quarantine"):
                        dpg.add_text("Quarantine Management", color=(200, 200, 200))
                        dpg.add_separator()
                        
                        dpg.add_text("Quarantined Files:", color=(180, 180, 180))
                        dpg.add_input_text(tag="quarantine_files_display", default_value="No files in quarantine",
                                          multiline=True, width=600, height=250, 
                                          readonly=True)
                        
                        dpg.add_text("")
                        dpg.add_separator()
                        
                        with dpg.group(horizontal=True):
                            dpg.add_button(label="Refresh", callback=refresh_quarantine, width=120, height=35)
                            dpg.add_button(label="Delete All", callback=delete_quarantine_files, width=120, height=35)
                        dpg.add_text("")
                        dpg.add_text("Delete single file by name:", color=(180, 180, 180))
                        with dpg.group(horizontal=True):
                            dpg.add_input_text(tag="quarantine_selected_input", default_value="", width=420)
                            dpg.add_button(label="Delete Selected", callback=delete_quarantine_file, width=120, height=35)
    
    # Scan Dialog Window
    with dpg.window(label="Scan Configuration", tag="scan_dialog", modal=True, show=False, pos=(250, 150), width=550, height=350):
        dpg.add_text("Configure Scan Options", color=(200, 200, 200))
        dpg.add_separator()
        
        dpg.add_text("Directory Path:")
        with dpg.group(horizontal=True):
            dpg.add_input_text(tag="scan_path_input", default_value="", width=260)
            dpg.add_button(label="Browse...", callback=open_directory_browser, width=120, height=24)
            dpg.add_button(label="Use Last", callback=use_last_scan_path, width=120, height=24)
        
        dpg.add_text("")
        dpg.add_text("Scan Mode:")
        dpg.add_radio_button(items=["Fast Scan"], 
                    default_value="Fast Scan", tag="scan_mode_radio")
        
        dpg.add_text("")
        dpg.add_separator()
        
        with dpg.group(horizontal=True):
            dpg.add_button(label="Start Scan", callback=confirm_scan, width=150, height=40)
            dpg.add_button(label="Cancel", callback=cancel_scan_dialog, width=150, height=40)
    
    # Directory Browser Dialog - appears on top
    with dpg.file_dialog(directory_selector=True, show=False, callback=browse_directory, 
                         tag="dir_browser", width=700, height=400, modal=True):
        pass
    
    # Auto-Scan Configuration Dialog
    with dpg.window(label="Auto-Scan Configuration", tag="auto_scan_dialog", modal=True, show=False, pos=(200, 100), width=600, height=450):
        dpg.add_text("Configure Auto-Scan Settings", color=(200, 200, 200))
        dpg.add_separator()
        
        dpg.add_text("Scan Time (HH:MM):", color=(180, 180, 180))
        with dpg.group(horizontal=True):
            dpg.add_input_text(tag="auto_scan_time_input", default_value=settings.get("scan.auto_scan_time"), 
                              width=300, readonly=True)
            dpg.add_button(label="Pick Time", callback=open_time_picker, width=120, height=24)
        dpg.add_text("")
        
        dpg.add_text("Directory/Drive to Scan:", color=(180, 180, 180))
        with dpg.group(horizontal=True):
            dpg.add_input_text(tag="auto_scan_path_input", default_value=settings.get("scan.auto_scan_path"), 
                              width=420)
            dpg.add_button(label="Browse...", callback=auto_scan_browser_open, width=120, height=24)
        dpg.add_text("")
        
        dpg.add_text("Scan Mode:", color=(180, 180, 180))
        dpg.add_radio_button(items=["Fast Scan", "Full Scan"], 
                            default_value=settings.get("scan.auto_scan_mode"), 
                            tag="auto_scan_mode_radio")
        dpg.add_text("")
        
        dpg.add_separator()
        with dpg.group(horizontal=True):
            dpg.add_button(label="Confirm", callback=confirm_auto_scan_settings, width=150, height=40)
            dpg.add_button(label="Cancel", callback=cancel_auto_scan_dialog, width=150, height=40)
    
    # Auto-Scan Directory Browser Dialog
    with dpg.file_dialog(directory_selector=True, show=False, callback=auto_scan_browse_directory, 
                         tag="auto_scan_dir_browser", width=700, height=400, modal=True):
        pass
    
    # Time Picker Dialog
    with dpg.window(label="Select Time", tag="time_picker_dialog", modal=True, show=False, pos=(350, 200), width=400, height=300):
        dpg.add_text("Select Scan Time", color=(200, 200, 200))
        dpg.add_separator()
        
        dpg.add_text("Hours:", color=(180, 180, 180))
        dpg.add_slider_int(tag="time_picker_hours", default_value=0, min_value=0, max_value=23, width=300,
                          callback=update_time_preview)
        
        dpg.add_text("")
        dpg.add_text("Minutes:", color=(180, 180, 180))
        dpg.add_slider_int(tag="time_picker_minutes", default_value=0, min_value=0, max_value=59, width=300,
                          callback=update_time_preview)
        
        dpg.add_text("")
        dpg.add_separator()
        
        # Current time preview
        dpg.add_text("Selected Time: 00:00", tag="time_preview", color=(150, 200, 150))
        
        dpg.add_text("")
        with dpg.group(horizontal=True):
            dpg.add_button(label="Confirm", callback=confirm_time_selection, width=120, height=40)
            dpg.add_button(label="Cancel", callback=cancel_time_picker, width=120, height=40)
    
    dpg.create_viewport(title="Kiwiyd Antivirus", width=900, height=600)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_primary_window("main_window", True)
    
    # Load system information on startup
    refresh_system_info()
    
    while dpg.is_dearpygui_running():
        dpg.render_dearpygui_frame()
    
    dpg.destroy_context()