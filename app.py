import dearpygui.dearpygui as dpg
import os
import threading

# Initialize DearPyGui
dpg.create_context()

# Global variables
output_text = "Welcome to Kiwiyd Antivirus\nSelect an action to begin...\n"
quarantine_log = "Quarantine Log:\n"
scan_in_progress = False
scan_directory_path = "test_files"
scan_mode = "Fast Scan"
quarantine_files_list = []  # Store quarantine files list

def append_output(message: str):
    """Append message to output display"""
    global output_text
    output_text += message + "\n"
    if dpg.does_item_exist("output_text"):
        dpg.set_value("output_text", output_text)

def append_quarantine_log(message: str):
    """Append message to quarantine log display"""
    global quarantine_log
    quarantine_log += message + "\n"
    if dpg.does_item_exist("quarantine_log_text"):
        dpg.set_value("quarantine_log_text", quarantine_log)

def browse_directory(sender, app_data):
    """Handle directory selection from file browser"""
    selected_path = app_data.get("file_path_name", "")
    if selected_path:
        dpg.set_value("scan_path_input", selected_path)
        append_output(f"✓ Directory selected: {selected_path}")

def open_directory_browser():
    """Open directory browser"""
    dpg.show_item("dir_browser")

def open_scan_dialog():
    """Open scan configuration dialog"""
    global scan_directory_path, scan_mode
    dpg.show_item("scan_dialog")

def confirm_scan():
    """Confirm and start scan with selected options"""
    global scan_directory_path, scan_mode, scan_in_progress
    
    # Get values from dialog
    scan_directory_path = dpg.get_value("scan_path_input")
    scan_mode = dpg.get_value("scan_mode_radio")
    
    if not scan_directory_path:
        append_output("✗ Error: Please specify a directory path")
        return
    
    dpg.hide_item("scan_dialog")
    
    if scan_in_progress:
        append_output("Scan already in progress...")
        return
    
    scan_in_progress = True
    dpg.set_value("output_text", f"Scan started...\nDirectory: {scan_directory_path}\nMode: {scan_mode}\n")
    
    def scan_thread():
        try:
            result = scan_directory(scan_directory_path)
            append_output(f"✓ Scan completed: {result}")
        except Exception as e:
            append_output(f"✗ Scan error: {str(e)}")
        finally:
            global scan_in_progress
            scan_in_progress = False
    
    thread = threading.Thread(target=scan_thread, daemon=True)
    thread.start()

def cancel_scan_dialog():
    """Cancel scan dialog"""
    dpg.hide_item("scan_dialog")

def start_scan():
    """Open scan dialog"""
    open_scan_dialog()

def load_quarantine():
    """Load quarantine module and get list of quarantined files"""
    global quarantine_files_list
    
    append_quarantine_log("[*] Loading Quarantine Module...")
    append_quarantine_log("[*] Sending request to core: Connect to Quarantine Module")
    
    # Simulate loading quarantine files
    quarantine_files_list = [
        "virus_file_1.exe",
        "malware_sample.bin",
        "trojan_detected.dll",
        "ransomware_threat.com"
    ]
    
    append_quarantine_log("[✓] Response from core: Module connected")
    append_quarantine_log(f"[✓] Quarantine loaded: {len(quarantine_files_list)} infected files found")
    
    # Update text display with quarantine files
    if dpg.does_item_exist("quarantine_files_text"):
        files_text = "\n".join(quarantine_files_list)
        dpg.set_value("quarantine_files_text", files_text)

def restore_files():
    """Restore all quarantined files"""
    if not quarantine_files_list:
        append_quarantine_log("✗ Error: No files in quarantine")
        return
    
    append_quarantine_log(f"[*] Processing restore request for {len(quarantine_files_list)} file(s)...")
    append_quarantine_log("[*] Sending request to core: Restore files")
    append_quarantine_log("\nFiles to restore:")
    for file in quarantine_files_list:
        append_quarantine_log(f"  - {file}")
    
    append_quarantine_log("\n[*] Processing request...")
    append_quarantine_log("[✓] Response from core: Restore completed")
    append_quarantine_log(f"[✓] Successfully restored {len(quarantine_files_list)} file(s)")

def delete_files():
    """Delete all quarantined files"""
    global quarantine_files_list
    
    if not quarantine_files_list:
        append_quarantine_log("✗ Error: No files in quarantine")
        return
    
    append_quarantine_log(f"[*] Processing delete request for {len(quarantine_files_list)} file(s)...")
    append_quarantine_log("[*] Sending request to core: Delete files")
    append_quarantine_log("\nFiles to delete:")
    for file in quarantine_files_list:
        append_quarantine_log(f"  - {file}")
    
    append_quarantine_log("\n[*] Processing request...")
    append_quarantine_log("[✓] Response from core: Delete completed")
    append_quarantine_log(f"[✓] Successfully deleted {len(quarantine_files_list)} file(s)")
    
    # Clear the quarantine
    quarantine_files_list = []
    if dpg.does_item_exist("quarantine_files_text"):
        dpg.set_value("quarantine_files_text", "")

def covid_19():
    """Load quarantine - calls load_quarantine function"""
    load_quarantine()

def update_definitions():
    """Update virus definitions"""
    append_output("[*] Checking for virus definition updates...")
    append_output("[*] Downloading latest definitions...")
    append_output("[✓] Virus definitions updated successfully")
    append_output("[✓] Database now contains latest threat signatures")

def settings():
    """Open settings window"""
    append_output("✓ Settings opened...")

def quit_app():
    """Close application"""
    dpg.stop_dearpygui()

if __name__ == "__main__":
    # Create window with proper layout
    with dpg.window(label="Kiwiyd Antivirus", tag="main_window", no_close=False, pos=(100, 100)):
        # Title
        dpg.add_text("Kiwiyd Antivirus", color=(200, 200, 200))
        dpg.add_text("Welcome to the test antivirus application", color=(150, 150, 150))
        
        dpg.add_separator()
        
        # Main container with two columns
        with dpg.group(horizontal=True):
            # LEFT COLUMN - Action Buttons
            with dpg.group(tag="left_panel"):
                dpg.add_text("Actions", color=(200, 200, 200))
                dpg.add_separator()
                
                dpg.add_button(label="Start Scan", callback=start_scan, width=200, height=50)
                dpg.add_text("")  # Spacer
                
                dpg.add_button(label="Update Database", callback=update_definitions, width=200, height=50)
                dpg.add_text("")  # Spacer
                
                dpg.add_button(label="Exit", callback=quit_app, width=200, height=50)
            
            # RIGHT COLUMN - Tabs and Content
            with dpg.group(tag="right_panel"):
                # Tab bar for Quarantine and Settings
                with dpg.tab_bar():
                    with dpg.tab(label="Scan Output"):
                        dpg.add_text("Output Log:")
                        dpg.add_input_text(tag="output_text", default_value=output_text, 
                                          multiline=True, width=480, height=350, 
                                          readonly=True)
                    
                    with dpg.tab(label="Quarantine"):
                        dpg.add_text("Quarantine Management", color=(200, 200, 200))
                        dpg.add_separator()
                        dpg.add_text("Quarantined Files:")
                        dpg.add_input_text(tag="quarantine_files_text", default_value="",
                                          multiline=True, width=470, height=120,
                                          readonly=True)
                        dpg.add_separator()
                        dpg.add_button(label="Load Quarantine", callback=load_quarantine, width=150, height=35)
                        dpg.add_button(label="Restore Files", callback=restore_files, width=150, height=35)
                        dpg.add_button(label="Delete Files", callback=delete_files, width=150, height=35)
                        dpg.add_separator()
                        dpg.add_text("Quarantine Log:", color=(180, 180, 180))
                        dpg.add_input_text(tag="quarantine_log_text", default_value=quarantine_log,
                                          multiline=True, width=470, height=120,
                                          readonly=True)
                    
                    with dpg.tab(label="Settings"):
                        dpg.add_text("Application Settings", color=(200, 200, 200))
                        dpg.add_separator()
                        dpg.add_checkbox(label="Enable Auto-Update")
                        dpg.add_checkbox(label="Enable Real-time Protection")
                        dpg.add_checkbox(label="Enable Notifications")
                        dpg.add_separator()
                        dpg.add_text("Scan Settings:", color=(180, 180, 180))
                        dpg.add_radio_button(items=["Fast Scan", "Full Scan", "Custom"], default_value="Fast Scan")
                        dpg.add_separator()
                        dpg.add_text("Thread Count:")
                        dpg.add_slider_int(label="Threads", default_value=4, min_value=1, max_value=16, width=250)
                        dpg.add_separator()
                        dpg.add_button(label="Save Settings", width=150, height=35)
                        dpg.add_button(label="Reset to Defaults", width=150, height=35)
    
    # Scan Dialog Window
    with dpg.window(label="Scan Configuration", tag="scan_dialog", modal=True, show=False, pos=(250, 150), width=550, height=350):
        dpg.add_text("Configure Scan Options", color=(200, 200, 200))
        dpg.add_separator()
        
        dpg.add_text("Directory Path:")
        with dpg.group(horizontal=True):
            dpg.add_input_text(tag="scan_path_input", default_value="test_files", width=380)
            dpg.add_button(label="Browse...", callback=open_directory_browser, width=120, height=24)
        
        dpg.add_text("")
        dpg.add_text("Scan Mode:")
        dpg.add_radio_button(items=["Fast Scan", "Full Scan", "Custom"], 
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
    
    dpg.create_viewport(title="Kiwiyd Antivirus", width=1000, height=700)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_primary_window("main_window", True)
    
    while dpg.is_dearpygui_running():
        dpg.render_dearpygui_frame()
    
    dpg.destroy_context()
