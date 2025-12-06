import csv
import unittest
import time
import os
from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, 'customerLogin.env')

load_dotenv(dotenv_path=env_path)

if os.getenv("BASE_URL") is None:
    raise Exception(f"LỖI: Không tìm thấy file '{env_path}' hoặc file rỗng!")

def load_csv_data(filename):
    rows = []
    csv_path = os.path.join(current_dir, filename)
    try:
        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
    except FileNotFoundError:
        print(f"LỖI: Không tìm thấy file CSV tại: {csv_path}")
    return rows

class CustomerLoginTest(unittest.TestCase):
    
    def clear_cache(self):
        self.driver.execute_cdp_cmd("Network.clearBrowserCache", {})
        self.driver.execute_cdp_cmd("Network.clearBrowserCookies", {})

    def setUp(self):
        service_obj = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service_obj)
        self.driver.implicitly_wait(10)
        self.driver.maximize_window()
        self.clear_cache()
        
        self.base_url = os.getenv("BASE_URL")

    def tearDown(self):
        self.driver.quit()

    def login_flow(self, user_name, expected_text):
        driver = self.driver
        wait = WebDriverWait(driver, 10)

        driver.get(self.base_url)
        
        cus_login_xpath = os.getenv("LOCATOR_BTN_CUSTOMER_LOGIN_XPATH")
        cus_login_btn = wait.until(EC.element_to_be_clickable((By.XPATH, cus_login_xpath)))
        cus_login_btn.click()

        user_select_id = os.getenv("LOCATOR_SELECT_USER_ID")
        dropdown_element = wait.until(EC.visibility_of_element_located((By.ID, user_select_id)))
        select_obj = Select(dropdown_element)

        all_options_text = [option.text for option in select_obj.options]

        if user_name in all_options_text:
            select_obj.select_by_visible_text(user_name)
            
            login_btn_xpath = os.getenv("LOCATOR_BTN_LOGIN_XPATH")
            login_btn = wait.until(EC.element_to_be_clickable((By.XPATH, login_btn_xpath)))
            login_btn.click()
            
            time.sleep(1)
            
            welcome_msg_class = os.getenv("LOCATOR_MSG_WELCOME_CLASS")
            welcome_msg = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, welcome_msg_class))).text
            self.assertIn(expected_text, welcome_msg)

        else:
            login_btn_xpath = os.getenv("LOCATOR_BTN_LOGIN_XPATH")
            login_buttons = driver.find_elements(By.XPATH, login_btn_xpath)

            is_login_visible = False
            if len(login_buttons) > 0:
                if login_buttons[0].is_displayed():
                    is_login_visible = True
            
            self.assertFalse(is_login_visible, "Lỗi: Nút Login vẫn hiện ra dù chưa chọn User hợp lệ!")

def generate_test_cases():
    csv_filename = os.getenv("CSV_FILE")
    
    if not csv_filename:
        return

    data_rows = load_csv_data(csv_filename) 

    for index, row in enumerate(data_rows):
        def test(self, row=row): 
            self.login_flow(
                row["userName"],
                row["expectedWelcomeText"]
            )
        
        safe_name = row['userName'].replace(" ", "_")
        test_name = f"test_login_{index+1}_{safe_name}"
        
        setattr(CustomerLoginTest, test_name, test)

generate_test_cases()

if __name__ == "__main__":
    unittest.main()