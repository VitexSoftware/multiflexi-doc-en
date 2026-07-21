#!/usr/bin/env python3
"""Capture screenshots of key MultiFlexi pages for the documentation
overview page "What is MultiFlexi".

Usage:
    MF_LOGIN=vitex MF_PASSWORD=secret python3 capture_screenshots.py

Environment variables:
    MF_BASE_URL   Base URL of the /src/ folder
                  (default: http://localhost/multiflexi-web5/src)
    MF_LOGIN      Login name        (required)
    MF_PASSWORD   Password          (required)
    MF_HEADLESS   "0" to show the browser window (default: headless)
    GECKODRIVER   geckodriver path  (default: /usr/bin/geckodriver)
"""
import os
import sys
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE = os.environ.get("MF_BASE_URL", "http://localhost/multiflexi-web5/src").rstrip("/")
LOGIN = os.environ.get("MF_LOGIN")
PASSWORD = os.environ.get("MF_PASSWORD")
GECKODRIVER = os.environ.get("GECKODRIVER", "/usr/bin/geckodriver")
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

if not LOGIN or not PASSWORD:
    sys.exit("Set MF_LOGIN and MF_PASSWORD environment variables.")

opts = Options()
if os.environ.get("MF_HEADLESS", "1") != "0":
    opts.add_argument("-headless")
drv = webdriver.Firefox(service=Service(GECKODRIVER), options=opts)
drv.set_window_size(1400, 900)


def screenshot(name, wait=2):
    """Save screenshot with given name after waiting."""
    time.sleep(wait)
    path = os.path.join(OUT_DIR, f"{name}.png")
    drv.save_screenshot(path)
    print(f"  saved: {path}")


try:
    # --- Login ---
    print("Logging in...")
    drv.get(f"{BASE}/login.php")
    time.sleep(1)
    btn = drv.find_element(By.ID, "signinbutton")
    form = btn.find_element(By.XPATH, "./ancestor::form[1]")
    form.find_element(By.NAME, "login").send_keys(LOGIN)
    form.find_element(By.NAME, "password").send_keys(PASSWORD)
    drv.execute_script("arguments[0].submit();", form)
    time.sleep(2)
    print(f"  logged in, URL: {drv.current_url}")

    # --- Dashboard ---
    print("Capturing dashboard...")
    drv.get(f"{BASE}/home.php")
    screenshot("dashboard", 3)

    # --- Applications listing ---
    print("Capturing applications listing...")
    drv.get(f"{BASE}/apps.php")
    screenshot("apps-listing", 3)

    # --- Companies listing ---
    print("Capturing companies listing...")
    drv.get(f"{BASE}/companies.php")
    screenshot("companies", 3)

    # --- Credential types ---
    print("Capturing credentials...")
    drv.get(f"{BASE}/credentialtypes.php")
    screenshot("credential-types", 3)

    # --- RunTemplates ---
    print("Capturing run templates...")
    drv.get(f"{BASE}/runtemplates.php")
    screenshot("runtemplates", 3)

    # --- Job list ---
    print("Capturing job list...")
    drv.get(f"{BASE}/jobs.php")
    screenshot("jobs", 3)

    print("All screenshots captured successfully.")
finally:
    drv.quit()
