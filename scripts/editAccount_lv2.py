import csv
import unittest
import time
import os

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

current_dir = os.path.dirname(os.path.abspath(__file__))

def load_csv_data():
    rows = []
    try:
        with open("../data/editAccount_lv2.csv", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
    except FileNotFoundError:
        print(f"LỖI: Không tìm thấy file ../data/editAccount_lv2.csv")
    return rows

class EditAccountTest(unittest.TestCase):

    def setUp(self):
        service_obj = Service(ChromeDriverManager().install())
        
        options = webdriver.ChromeOptions()
        
        prefs = {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "profile.password_manager_leak_detection": False,
            "safebrowsing.enabled": False,
            "safebrowsing.disable_download_protection": True,
            "profile.default_content_settings.popups": 0,
            "profile.default_content_setting_values.notifications": 2
        }
        
        options.add_experimental_option("prefs", prefs)
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-features=PasswordLeakDetection,SafeBrowsing")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(service=service_obj, options=options)
        self.driver.implicitly_wait(10)
        self.driver.maximize_window()
        

    def tearDown(self):
        self.driver.quit()

    def login(self, row_data):
        driver = self.driver
        wait = WebDriverWait(driver, 10)
        
        base_url = row_data['BASE_URL']
        driver.get(base_url)
        
        email_id = row_data['LOCATOR_INPUT_EMAIL_ID']
        test_email = row_data['TEST_EMAIL']
        
        email_input = wait.until(EC.visibility_of_element_located((By.ID, email_id)))
        email_input.clear()
        email_input.send_keys(test_email)
        
        pass_id = row_data['LOCATOR_INPUT_PASSWORD_ID']
        test_pass = row_data['TEST_PASSWORD']
        
        pass_input = driver.find_element(By.ID, pass_id)
        pass_input.clear()
        pass_input.send_keys(test_pass)
        
        login_xpath = row_data['LOCATOR_BTN_LOGIN_XPATH']
        login_btn = driver.find_element(By.XPATH, login_xpath)
        login_btn.click()

    def edit_account_flow(self, row_data):
        driver = self.driver
        wait = WebDriverWait(driver, 30) 

        self.login(row_data)

        edit_link_text = row_data['LOCATOR_LINK_EDIT_TEXT']
        edit_link = wait.until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, edit_link_text)))
        edit_link.click()

        fname_id = row_data['LOCATOR_INPUT_FIRSTNAME_ID']
        fname_input = wait.until(EC.visibility_of_element_located((By.ID, fname_id)))
        
        phone_id = row_data['LOCATOR_INPUT_TELEPHONE_ID']
        phone_input = driver.find_element(By.ID, phone_id)

        fname_input.clear()
        fname_input.send_keys(row_data['firstName'])
        
        phone_input.clear()
        phone_input.send_keys(row_data['telephone'])

        continue_xpath = row_data['LOCATOR_BTN_CONTINUE_XPATH']
        continue_btn = driver.find_element(By.XPATH, continue_xpath)
        continue_btn.click()

        expected_type = row_data['expectedType']
        expected_msg = row_data['expectedMessage']

        if expected_type == "success":
            try:
                wait.until(EC.url_contains("route=account/account"))
            except:
                self.fail("Form submit quá lâu hoặc không thành công, chưa chuyển hướng về trang Account.")

            success_class = row_data['LOCATOR_MSG_SUCCESS_CLASS']
            success_alert = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, success_class)))
            self.assertIn(expected_msg, success_alert.text)

        else:
            error_xpath = f"//div[contains(@class, 'text-danger') and contains(text(), '{expected_msg}')]"
            try:
                error_element = wait.until(EC.visibility_of_element_located((By.XPATH, error_xpath)))
                self.assertTrue(error_element.is_displayed())
            except:
                self.fail(f"Fail: Không tìm thấy thông báo lỗi mong đợi: '{expected_msg}'")

def generate_test_cases():
    
    data_rows = load_csv_data() 
    
    if not data_rows:
        print("Không có dữ liệu để chạy test.")
        return

    for index, row in enumerate(data_rows):
        def test(self, row=row): 
            self.edit_account_flow(row)
        
        safe_name = "Valid" if row['expectedType'] == 'success' else "Invalid"
        test_name = f"test_edit_{index+1}_{safe_name}"
        
        setattr(EditAccountTest, test_name, test)

generate_test_cases()

if __name__ == "__main__":
    unittest.main()