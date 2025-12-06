import csv
import unittest
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
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
        self.base_url = "https://www.globalsqa.com/angularJs-protractor/BankingProject/#/login"

    def tearDown(self):
        self.driver.quit()

    def login_flow(self, user_name, expected_text):
        driver = self.driver
        wait = WebDriverWait(driver, 10)

        driver.get(self.base_url)
        cus_login_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Customer Login')]")))
        cus_login_btn.click()

        dropdown_element = wait.until(EC.visibility_of_element_located((By.ID, "userSelect")))
        select_obj = Select(dropdown_element)

        all_options_text = [option.text for option in select_obj.options]

        if user_name in all_options_text:
            select_obj.select_by_visible_text(user_name)
            
            login_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Login']")))
            login_btn.click()
            
            time.sleep(1)
            
            welcome_msg = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "fontBig"))).text
            self.assertIn(expected_text, welcome_msg)

        else:
            login_buttons = driver.find_elements(By.XPATH, "//button[text()='Login']")

            is_login_visible = False
            if len(login_buttons) > 0:
                if login_buttons[0].is_displayed():
                    is_login_visible = True
            
            self.assertFalse(is_login_visible, "Lỗi: Nút Login vẫn hiện ra dù chưa chọn User hợp lệ!")

def generate_test_cases():
    print("Chạy testcase customerLogin.py")
    data_rows = load_csv_data("../data/customerLogin.csv") 

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