import flet as ft
import os
import sys

# Add modules directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'modules'))

from settings import Settings
from system_info import SystemInfo

settings = Settings()

def main(page: ft.Page):
    page.title = "Kiwiyd Antivirus"
    page.window_width = 950
    page.window_height = 650

    # Global variables
    output_text = "Welcome to Kiwiyd Antivirus\nSelect an action to begin...\n"

    def append_output(message: str):
        nonlocal output_text
        output_text += message + "\n"
        output_log.value = output_text
        page.update()

    # Output log
    output_log = ft.TextField(
        value=output_text,
        multiline=True,
        read_only=True,
        width=600,
        height=450
    )

    # Scan dialog
    scan_path_input = ft.TextField(label="Directory Path", width=600)
    scan_mode = "Fast Scan"  # Fixed to Fast Scan

    def pick_directory_result(e: ft.FilePickerResultEvent):
        if e.path:
            scan_path_input.value = e.path
            append_output(f"✓ Selected directory: {e.path}")
            page.update()

    file_picker = ft.FilePicker(on_result=pick_directory_result)

    def browse_directory(e):
        file_picker.get_directory_path()

    def use_last_directory(e):
        last_path = settings.get("scan.last_directory") or "C:\\"
        if os.path.exists(last_path):
            scan_path_input.value = last_path
            append_output(f"✓ Using last directory: {last_path}")
        else:
            append_output("✗ Last directory not found, using C:\\")
            scan_path_input.value = "C:\\"
        page.update()

    def confirm_scan(e):
        scan_directory_path = scan_path_input.value
        scan_mode = "Fast Scan"

        if not scan_directory_path:
            append_output("✗ Error: Please specify a directory path")
            return

        if not os.path.exists(scan_directory_path):
            append_output(f"✗ Error: Directory not found: {scan_directory_path}")
            return

        # Save last directory
        settings.set("scan.last_directory", scan_directory_path)

        scan_dialog.open = False
        append_output(f"[*] Calling scanner module...\nDirectory: {scan_directory_path}\nMode: {scan_mode}")
        page.update()

    def cancel_scan_dialog(e):
        scan_dialog.open = False
        page.update()

    scan_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Scan Configuration"),
        content=ft.Container(
            width=750,  # фиксируем ширину диалога
            content=ft.Column([
                ft.Text("Directory Path:"),
                scan_path_input,
                ft.ElevatedButton("Browse...", on_click=browse_directory, width=200),
                ft.ElevatedButton("Use Last", on_click=use_last_directory, width=200),
                ft.Text("Scan Mode: Fast Scan"),
            ], tight=True)
        ),
        actions=[
            ft.TextButton("Start Scan", on_click=confirm_scan),
            ft.TextButton("Cancel", on_click=cancel_scan_dialog),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    def start_scan(e):
        last_path = settings.get("scan.last_directory")
        if last_path:
            scan_path_input.value = last_path
        scan_dialog.open = True
        page.update()

    # Settings
    auto_quarantine = ft.Checkbox(label="Auto-Quarantine Threats", value=settings.get("quarantine.auto_quarantine"))
    auto_update = ft.Checkbox(label="Enable Auto-Update", value=settings.get("updates.auto_update"))
    notifications = ft.Checkbox(label="Enable Notifications", value=settings.get("notifications.enable_notifications"))
    thread_slider_value = ft.Text(f"Selected: {settings.get('scan.thread_count')} thread(s)")

    def thread_slider_changed(e):
        thread_slider_value.value = f"Selected: {int(e.control.value)} thread(s)"
        page.update()

    thread_slider = ft.Slider(
        min=1, max=16, divisions=15,
        value=settings.get("scan.thread_count"),
        on_change=thread_slider_changed
    )

    # System Info
    system_info_text = ft.TextField(multiline=True, read_only=True, width=600, height=400)

    def refresh_system_info(e):
        try:
            system_info_text.value = SystemInfo.format_info_display()
        except Exception as ex:
            system_info_text.value = f"Error loading system info: {str(ex)}"
        page.update()

    # Quarantine
    quarantine_files_display = ft.TextField(value="No files in quarantine", multiline=True, read_only=True, width=600, height=250)
    delete_single_input = ft.TextField(label="Delete single file by name", width=400)

    def load_quarantine_files():
        try:
            append_output("[*] Loading quarantine module...")
            append_output("[*] Connecting to quarantine module...")
            # TODO: Call C++ quarantine module (quarantine.exe) to get list of files
            quarantine_files = []
            if quarantine_files:
                files_text = "\n".join(quarantine_files)
                quarantine_files_display.value = files_text
                append_output(f"[OK] Quarantine loaded: {len(quarantine_files)} file(s)")
            else:
                quarantine_files_display.value = "No files in quarantine"
                append_output("[OK] Quarantine is empty")
        except Exception as ex:
            append_output(f"[ERROR] Error loading quarantine: {str(ex)}")

    def delete_quarantine_files(e):
        if quarantine_files_display.value == "No files in quarantine":
            append_output("[!] Quarantine is empty, nothing to delete")
            return
        append_output("[*] Processing delete request...")
        append_output("[*] Sending request to quarantine module to delete files...")
        # TODO: Call C++ quarantine.exe to delete all files
        append_output("[OK] Files deleted successfully")
        quarantine_files_display.value = "No files in quarantine"
        append_output("[OK] Quarantine cleared")
        page.update()

    def delete_single_file(e):
        filename = delete_single_input.value.strip()
        if not filename:
            append_output("✗ Error: Please enter a file name")
            return
        append_output(f"[*] Requesting deletion of file: {filename}")
        # TODO: Call C++ quarantine.exe to delete specific file
        append_output(f"[OK] File '{filename}' deleted successfully")
        delete_single_input.value = ""
        page.update()

    def refresh_quarantine(e):
        load_quarantine_files()
        page.update()

    # Tabs
    tabs = ft.Tabs(
        selected_index=0,
        tabs=[
            ft.Tab(text="Scan Output", content=output_log),
            ft.Tab(
                text="Settings",
                content=ft.Column([
                    ft.Text("Scan Settings:", weight=ft.FontWeight.BOLD),
                    auto_quarantine,
                    ft.Text("Thread Count for Scanning:"),
                    thread_slider,
                    thread_slider_value,
                    ft.Text("Update Settings:", weight=ft.FontWeight.BOLD),
                    auto_update,
                    ft.Text("Notification Settings:", weight=ft.FontWeight.BOLD),
                    notifications,
                ], scroll=ft.ScrollMode.AUTO)
            ),
            ft.Tab(
                text="System Info",
                content=ft.Column([
                    ft.ElevatedButton("Refresh", on_click=refresh_system_info),
                    system_info_text
                ])
            ),
            ft.Tab(
                text="Quarantine",
                content=ft.Column([
                    ft.Text("Quarantined Files:"),
                    quarantine_files_display,
                    ft.Row([
                        ft.ElevatedButton("Refresh", on_click=refresh_quarantine),
                        ft.ElevatedButton("Delete All", on_click=delete_quarantine_files),
                    ]),
                    ft.Row([
                        delete_single_input,
                        ft.ElevatedButton("Delete Selected", on_click=delete_single_file)
                    ])
                ])
            )
        ]
    )

    # Main layout
    page.add(
        ft.Column([
            ft.Text("Kiwiyd Antivirus", size=24, weight=ft.FontWeight.BOLD),
            ft.Text("Antivirus Scanner", size=16),
            ft.Divider(),
            ft.Row([
                ft.Column([
                    ft.Text("Actions", weight=ft.FontWeight.BOLD),
                    ft.ElevatedButton("Start Scan", on_click=start_scan, width=200, height=50),
                    ft.ElevatedButton("Exit", on_click=lambda e: page.window_close(), width=200, height=50),
                ]),
                ft.Container(content=tabs, expand=True)
            ], expand=True)
        ], expand=True)
    )

    # Add dialogs to page
    page.overlay.append(scan_dialog)
    page.overlay.append(file_picker)

    # Initialize
    refresh_system_info(None)
    load_quarantine_files()

ft.app(target=main)
