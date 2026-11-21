"""
run.py
======
Convenient entrypoint to launch the ExpensePulse web application.
Automatically opens the local web browser upon startup.
"""

import sys
import os
import webbrowser
import threading
import time

def open_browser():
    time.sleep(1.2)
    webbrowser.open("http://127.0.0.1:5000")

if __name__ == "__main__":
    from app import app
    print("=" * 65)
    print("  ExpensePulse - Expense Analyzer & Pattern Reporting")
    print("  Running at: http://127.0.0.1:5000")
    print("  Press Ctrl+C to terminate the server")
    print("=" * 65)
    
    # Launch browser in a background daemon thread
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Start web server
    app.run(host="127.0.0.1", port=5000, debug=False)
