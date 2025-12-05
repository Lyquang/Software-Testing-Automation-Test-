import csv
import unittest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def load_csv_data(filename):
    rows = []
    try:
        with open(filename, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
    except FileNotFoundError:
        print(f"Không tìm thấy file {filename}")
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
        self.base_url = "https://ecommerce-playground.lambdatest.io/index.php?route=account/login"

    def tearDown(self):
        self.driver.quit()

    def login(self):
        driver = self.driver
        wait = WebDriverWait(driver, 10)
        
        driver.get(self.base_url)
        
        email_input = wait.until(EC.visibility_of_element_located((By.ID, "input-email")))
        email_input.clear()
        email_input.send_keys("a@mymail.com")
        
        pass_input = driver.find_element(By.ID, "input-password")
        pass_input.clear()
        pass_input.send_keys("1234")
        
        login_btn = driver.find_element(By.XPATH, "//input[@value='Login']")
        login_btn.click()

    def edit_account_flow(self, first_name, telephone, expected_type, expected_msg):
        driver = self.driver
        wait = WebDriverWait(driver, 30) 

        self.login()

        edit_link = wait.until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "Edit your account")))
        edit_link.click()

        fname_input = wait.until(EC.visibility_of_element_located((By.ID, "input-firstname")))
        phone_input = driver.find_element(By.ID, "input-telephone")

        fname_input.clear()
        fname_input.send_keys(first_name)
        
        phone_input.clear()
        phone_input.send_keys(telephone)

        continue_btn = driver.find_element(By.XPATH, "//input[@value='Continue']")
        continue_btn.click()

        if expected_type == "success":
            
            try:
                wait.until(EC.url_contains("route=account/account"))
            except:
                self.fail("Form submit quá lâu hoặc không thành công, chưa chuyển hướng về trang Account.")

            success_alert = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "alert-success")))
            self.assertIn(expected_msg, success_alert.text)

        else:
            error_xpath = f"//div[contains(@class, 'text-danger') and contains(text(), '{expected_msg}')]"
            try:
                error_element = wait.until(EC.visibility_of_element_located((By.XPATH, error_xpath)))
                self.assertTrue(error_element.is_displayed())
            except:
                driver.save_screenshot(f"error_fail_{first_name}.png")
                self.fail(f"Fail: Không tìm thấy thông báo lỗi mong đợi: '{expected_msg}'")

def generate_test_cases():
    data_rows = load_csv_data("editAccount.csv") 

    for index, row in enumerate(data_rows):
        def test(self, row=row): 
            self.edit_account_flow(
                row["firstName"],
                row["telephone"],
                row["expectedType"],
                row["expectedMessage"]
            )
        
        safe_name = "Valid" if row['expectedType'] == 'success' else "Invalid"
        test_name = f"test_edit_{index+1}_{safe_name}"
        
        setattr(EditAccountTest, test_name, test)

generate_test_cases()

if __name__ == "__main__":
    unittest.main()