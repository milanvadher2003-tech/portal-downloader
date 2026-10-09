"""
Runtime hook — Playwright ko batata hai ki bundled Chromium kahan hai
"""
import os
import sys
import tempfile

# PyInstaller temp folder (_MEIxxxxxx)
if getattr(sys, 'frozen', False):
    bundle_dir = sys._MEIPASS
else:
    bundle_dir = os.path.dirname(os.path.abspath(__file__))

# Playwright browser path set karo
bundled_browsers = os.path.join(bundle_dir, 'playwright_browsers')

if os.path.exists(bundled_browsers):
    os.environ['PLAYWRIGHT_BROWSERS_PATH'] = bundled_browsers
