"""
Utility functions for browser-related operations.
"""
import os
import platform
import webbrowser


def open_html_report(file_path):
    """
    Open an HTML report in the default web browser.

    Args:
        file_path: Path to the HTML file to open

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Convert to absolute path if relative
        abs_path = os.path.abspath(file_path)

        # Convert file path to URL format based on OS
        if platform.system() == 'Windows':
            url = f'file:///{abs_path}'
        else:
            url = f'file://{abs_path}'

        # Open in default browser
        webbrowser.open(url)
        print(f"Opened report in browser: {abs_path}")
        return True

    except Exception as e:
        print(f"Error opening HTML report: {str(e)}")
        return False