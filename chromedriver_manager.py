import json
import os
import platform
import shutil
import subprocess
import urllib.request
from urllib.request import urlopen
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from random import choice

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    

# Get script directory
script_dir = os.getcwd()

OS_INFO = {
    'Linux': {
        'chrome_zip': 'chrome-linux64.zip',
        'chromedriver_zip': 'chromedriver_linux64.zip',
        'unzip': 'unzip',
        'json_index': 0,
        'osname': 'lin',
        'exe_name': "",
    },
    'Darwin': {
        'chrome_zip': 'chrome-mac.zip',
        'chromedriver_zip': 'chromedriver_mac64.zip',
        'unzip': 'unzip',
        'json_index': 2,
        'osname': 'mac',
        'exe_name': "",
    },
    'Windows': {
        'chrome_zip': 'chrome.zip',
        'chromedriver_zip': 'chromedriver_win32.zip',
        'unzip': None,
        'json_index': 3,
        'osname': 'win',
        'exe_name': ".exe",
    },
}

def get_platform_info():
  """Returns a dictionary containing platform-specific information. 

  Raises: 
     Exception: If the current platform is unsupported. 
  """
  system = platform.system()
  try:
      return OS_INFO[system]
  except KeyError:
      raise Exception(f"Unsupported platform: {system}")
    
    

def download_and_unzip(url, filename, unzip_cmd=None):
  """Downloads a file and unzips it if necessary.

  Args:
      url: The URL of the file to download.
      filename: The filename to save the downloaded file as.
      unzip_cmd: The command to use for unzipping (optional).

  Raises:
      OSError: If an error occurs during download or extraction.
  """
  
  if os.path.exists(filename):
    print(f"{bcolors.WARNING} ...{bcolors.OKCYAN}{filename} {bcolors.WARNING}already exists. Skipping download. {bcolors.ENDC}")
    return
  
  print(f"Downloading {bcolors.OKCYAN}{filename}{bcolors.WARNING} ... {bcolors.ENDC}")
  with urlopen(url) as response:
    data = response.read()
  with open(filename, 'wb') as f:
    f.write(data)
    
  print(f"{bcolors.WARNING} ... Extracting: {bcolors.OKCYAN}{filename} {bcolors.ENDC}")
  if unzip_cmd:
      subprocess.run([unzip_cmd, filename])
  else:
      # Use shutil for all platforms (if applicable)
      try:
          shutil.unpack_archive(filename, 'zip', filename[:-4])
          print(f"{bcolors.WARNING} ... Extracted to: {bcolors.OKCYAN}{filename[:-4]} {bcolors.ENDC}")
      except (OSError, shutil.ReadError):
          # Fallback to platform-specific extraction (if needed)
          if unzip_cmd:
              subprocess.run([unzip_cmd, filename])
          else:
              raise Exception(f"Failed to extract {filename} using shutil or platform-specific command.")


def find_executable(base_dir, file_names):
  """Searches for executables (chromedriver, chrome) within a directory and its subdirectories.

  Args:
      base_dir: The base directory to search
      file_names: A list of filenames to search for

  Returns:
      A list of found executable paths.
  """
  found_paths = []
  for dirpath, _, filenames in os.walk(base_dir):
      for filename in filenames:
          if filename in file_names:
              filepath = os.path.join(dirpath, filename)
              if os.access(filepath, os.X_OK):  
                  found_paths.append(filepath)
  if len(found_paths) < len(file_names):
      print(f"Found only {len(found_paths)} executable")
      found_paths.append(None)
      
  return found_paths

def move_driver(source_path, target_dir):
  """Moves a driver file to the target directory.

  Args:
      source_path: The path to the driver file.
      target_dir: The target directory to move the file to.
  """
  try:
    #shutil.move(source_path, target_dir)
    shutil.copy2(source_path, target_dir)
    print(f"{bcolors.WARNING} Moved {bcolors.OKCYAN}{source_path} {bcolors.WARNING}to {bcolors.OKCYAN}{target_dir} {bcolors.WARNING}successfully. {bcolors.ENDC}")
  except Exception as e:
    print(f"{bcolors.FAIL} ... Error moving chromedriver: {bcolors.OKCYAN}{e} {bcolors.ENDC}")



def get_latest_chromedriver_version():
  """Retrieves the latest ChromeDriver version from the official website."""

  url = "https://chromedriver.storage.googleapis.com/LATEST_RELEASE"
  try:
    with urllib.request.urlopen(url) as response:
      return response.read().decode().strip()
  except Exception as e:
    print(f"Error getting latest ChromeDriver version: {e}")
    return None
  
  

def download_driver():
  """Downloads the appropriate Chrome and ChromeDriver versions based on the platform.
  
  Returns:
      A tuple containing exe_name, osname, chromedriver_path, and chrome_binary_path.
  """
  platform_info = get_platform_info()
  chromedriver_version = get_latest_chromedriver_version()
  json_url = 'https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json'
  exe_name = platform_info['exe_name']
  osname = platform_info['osname']
  chrome_binary_path = ""

  with urlopen(json_url) as response:
    data = json.loads(response.read().decode())
    chrome_url = data['channels']['Stable']['downloads']['chrome'][platform_info['json_index']]['url']
    chromedriver_url = data['channels']['Stable']['downloads']['chromedriver'][platform_info['json_index']]['url']
    chromedriver_version = data['channels']['Stable']['version']

    print(f"{bcolors.WARNING} Current Chromedriver Version Online: {bcolors.OKCYAN}{chromedriver_version} {bcolors.ENDC}")
    
    version_filename = "version.txt"
    
    try:
        with open(version_filename, 'r') as file:
            lines = file.readlines()
            variables = {}
            for line in lines:
                key, value = line.strip().split('=')
                variables[key] = value
            previous_version, previous_osname= variables.get('chromedriver_version', "0"), variables.get('osname', None)
            print(f"{bcolors.WARNING} Previous Chromedriver Version Local: {bcolors.OKCYAN}{previous_version} {bcolors.ENDC}")
    except Exception as e:
        print(f"{bcolors.WARNING}Error reading variables from file: {bcolors.FAIL}{e}{bcolors.ENDC}")
        previous_version, previous_osname = None, None
        
        
    try:
        with open(version_filename, 'w') as file:
            file.write(f"chromedriver_version={chromedriver_version}\n")
            file.write(f"osname={osname}")
    except Exception as e:
        print(f"{bcolors.WARNING}Error writing variables to file: {bcolors.FAIL}{e}{bcolors.ENDC}")
        
    if chromedriver_version != previous_version or osname!= previous_osname:
      import glob
      try:
        for filename in glob.glob("chrome*") + glob.glob("chromedriver*"):
            if os.path.isdir(filename):
                shutil.rmtree(filename)  # Recursively remove directory
            else:
                os.unlink(filename)  # Remove file
      except Exception as e:
        print(f"Error removing old files: {e}")
        
      shutil.rmtree("patched_drivers", ignore_errors=True)
  
  download_and_unzip(chrome_url, platform_info['chrome_zip'], platform_info['unzip'])
  download_and_unzip(chromedriver_url, platform_info['chromedriver_zip'], platform_info['unzip'])   
  
  if not platform.system() == 'Windows':
    # Search for chromedriver in sibling directories
    script_dir = os.getcwd()
    chromedriver_path, chrome_binary_path = find_executable(script_dir, ['chromedriver', 'chrome'])
    if chromedriver_path:
        os.chmod(chromedriver_path, 0o755)
        print(f"{bcolors.OKBLUE}chromedriver_path: {chromedriver_path}. {bcolors.ENDC}")

    if chrome_binary_path:  
        os.chmod(chrome_binary_path, 0o755)
        move_driver(chrome_binary_path, script_dir)
        chrome_binary_path_new = os.path.join(script_dir, f'chrome{exe_name}')
        print(f"{bcolors.OKBLUE}chrome_binary_path_new: {chrome_binary_path_new} {bcolors.ENDC}")
        os.chmod(chrome_binary_path_new, 0o755)

  return exe_name, osname, chromedriver_path, chrome_binary_path

  
def get_driver(viewports= ['2560,1440', '1920,1080', '1920,1440'],
            chromedriver_path=None, chrome_binary_path=None, 
            user_agent=None, **kwargs):
    """Creates a WebDriver instance with specified options.

    Args:
        viewports: A list of viewport sizes.
        chromedriver_path: The path to the ChromeDriver executable.
        chrome_binary_path: The path to the Chrome binary.
        user_agent: The user agent string.
        **kwargs: Additional keyword arguments for WebDriver options.

    Returns:
        A WebDriver instance.
    """
    
    options = webdriver.ChromeOptions()

    print(f"user_agent: {user_agent}")
    if kwargs.pop('background', None):
        options.add_argument("--headless")
        
    args = [
        f"--window-size={choice(viewports)}",
        "--log-level=3",
        "--mute-audio",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-features=UserAgentClientHint",
        "--disable-web-security",
        "--disable-extensions"
    ]
    for arg in args:
        options.add_argument(arg)

    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    options.add_experimental_option('useAutomationExtension', False)

    prefs = {"intl.accept_languages": 'en_US,en',
                "credentials_enable_service": False,
                "profile.password_manager_enabled": False,
                "profile.default_content_setting_values.notifications": 2,
                "download_restrictions": 3
                }
    options.add_experimental_option("prefs", prefs)

    options.add_argument(f"user-agent={user_agent}") if user_agent else None
    options.add_argument("--mute-audio")
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-features=UserAgentClientHint')
    options.add_argument("--disable-web-security")

    webdriver.DesiredCapabilities.CHROME['loggingPrefs'] = {'driver': 'OFF', 'server': 'OFF', 'browser': 'OFF'}


    # Set binary location and service
    if chrome_binary_path:
        options.binary_location = chrome_binary_path

    service = Service(chromedriver_path)

    return webdriver.Chrome(
        service=service, 
        options=options, 
        )
             
# Example Usage
if __name__ == "__main__":
    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
    exe_name, osname, chromedriver_path, chrome_binary_path = download_driver()
    browser = get_driver(chromedriver_path=chromedriver_path, chrome_binary_path=chrome_binary_path, user_agent=user_agent)

    browser.get("https://www.scrapethissite.com/")

    # Wait for the tagline to appear
    tagline = browser.find_element(By.CSS_SELECTOR, "#hero > div > div > div > p")
    print(f"{tagline.text}")

    

