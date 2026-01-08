import json
import subprocess
import sys
import random
import string
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

def random_string(length):
    return ''.join(random.choices(string.ascii_letters, k=length))

def bash_command(cmd):
    subprocess.run(cmd, shell=True, executable='/bin/bash', check=True)

# Validate arguments
if len(sys.argv) < 4:
    print("Usage:")
    print(" 1. Selenium Remote Server IP")
    print(" 2. Target App IP")
    print(" 3. HTML Output Path for Nikto")
    sys.exit(1)

selenium_ip = sys.argv[1]
target_ip = sys.argv[2]
output_path = sys.argv[3]

myusername = random_string(8)
mypassword = random_string(12)

# Configure WebDriver
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")

print("[*] Launching headless Chrome via Selenium Grid...")
driver = webdriver.Remote(
    command_executor=f"http://{selenium_ip}:4444/wd/hub",
    options=chrome_options
)

try:
    print("[*] Navigating to registration page...")
    driver.get(f"http://{target_ip}:10007/login")
    driver.find_element(By.XPATH, "/html/body/div/div/div/form/center[3]/a").click()

    print("[*] Registering a new user...")
    driver.find_element(By.NAME, "username").send_keys(myusername)
    driver.find_element(By.NAME, "password1").send_keys(mypassword)
    driver.find_element(By.NAME, "password2").send_keys(mypassword + Keys.RETURN)

    assert "Login" in driver.find_element(By.XPATH, '/html/body/div/div/div/center[2]/h4').text
    print(f"[+] User '{myusername}' created successfully.")

    print("[*] Logging in...")
    driver.get(f"http://{target_ip}:10007/login")
    driver.find_element(By.NAME, "username").send_keys(myusername)
    driver.find_element(By.NAME, "password").send_keys(mypassword + Keys.RETURN)

    assert "Last gossips" in driver.find_element(By.XPATH, "/html/body/div/div/div[1]/h1").text
    print(f"[+] Logged in as '{myusername}'. Extracting cookies...")

    cookies = driver.get_cookies()
    cookie_string = "STATIC-COOKIE="
    for cookie in cookies:
        cookie_string += f'"{cookie["name"]}"="{cookie["value"]}" '

    # Update Nikto config securely
    nikto_config_path = "~/nikto-config.txt"
    bash_command(f"cp /etc/nikto/config.txt {nikto_config_path}")
    bash_command(f"echo '{cookie_string.strip()}' >> {nikto_config_path}")
    print("[+] Auth cookie added to Nikto config.")

    # Run Nikto Authenticated Scan
    print("[*] Starting Nikto authenticated scan...")
    bash_command(
        f"nikto -ask no -config {nikto_config_path} -Format html "
        f"-h http://{target_ip}:10007/gossip -output {output_path}"
    )
    print(f"[✓] Nikto scan completed. Report saved at {output_path}")

except Exception as e:
    print(f"[!] Error: {e}")
    sys.exit(1)

finally:
    driver.quit()
