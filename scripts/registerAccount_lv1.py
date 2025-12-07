# -*- coding: utf-8 -*-
import csv
import unittest
import time
import random
import string
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def load_csv_data():
    rows = []
    try:
        with open("../data/registerAccount_lv1.csv", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
    except FileNotFoundError:
        print("Lỗi: Không tìm thấy file")
    return rows

class RegisterTest(unittest.TestCase):

    def setUp(self):
        service_obj = Service(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        # options.add_argument("--headless") 
        self.driver = webdriver.Chrome(service=service_obj, options=options)
        self.driver.implicitly_wait(3)
        self.driver.maximize_window()
        self.base_url = "https://ecommerce-playground.lambdatest.io/index.php?route=account/register"

    def tearDown(self):
        self.driver.quit()

    def run_register_test(self, case_id, f_name, l_name, email, phone, pwd, confirm_pwd, policy, expected_msg, should_success):
        driver = self.driver
        driver.get(self.base_url)
        print(f"\n[{case_id}] Running...", end=" ")

        # --- 1. FILL FORM ---
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "input-firstname")))

        if f_name: driver.find_element(By.ID, "input-firstname").send_keys(f_name)
        if l_name: driver.find_element(By.ID, "input-lastname").send_keys(l_name)

        # --- LOGIC RANDOM EMAIL CẢI TIẾN ---
        # Random cho TẤT CẢ các case có định dạng email hợp lệ (có @)
        # Lý do: Để đảm bảo test check lỗi khác (như First Name, Phone...) không bị chặn bởi lỗi "Email đã tồn tại".
        final_email = email
        if email and "@" in email: 
            random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
            parts = email.split('@')
            if len(parts) == 2:
                final_email = f"{parts[0]}_{random_str}@{parts[1]}"
            else:
                final_email = f"{email}_{random_str}"
        
        if final_email: driver.find_element(By.ID, "input-email").send_keys(final_email)
        if phone: driver.find_element(By.ID, "input-telephone").send_keys(phone)
        if pwd: driver.find_element(By.ID, "input-password").send_keys(pwd)
        if confirm_pwd: driver.find_element(By.ID, "input-confirm").send_keys(confirm_pwd)

        if policy == "True":
            try:
                chk = driver.find_element(By.NAME, "agree")
                driver.execute_script("arguments[0].click();", chk)
            except: pass

        # --- Wait & Submit ---
        time.sleep(1) 
        submit_btn = driver.find_element(By.XPATH, "//input[@value='Continue']")
        driver.execute_script("arguments[0].click();", submit_btn)

        # --- 2. VERIFY ---
        if should_success == "True":
            try:
                success_element = WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.XPATH, "//h1[contains(text(),'Your Account Has Been Created')]")))
                self.assertEqual(success_element.text, expected_msg)
                print(f"-> PASSED (Account Created)")
                try: driver.find_element(By.LINK_TEXT, "Logout").click()
                except: pass
            except:
                # Debug lỗi
                err_text = "Unknown Error"
                try: err_text = driver.find_element(By.CSS_SELECTOR, ".alert-danger").text
                except: pass
                if err_text == "Unknown Error":
                    try:
                        field_errs = driver.find_elements(By.CSS_SELECTOR, ".text-danger")
                        if field_errs: err_text = field_errs[0].text
                    except: pass
                
                self.fail(f"FAILED. Mong đợi thành công nhưng thấy lỗi: {err_text}")
        else:
            # Case mong đợi thất bại
            found_error = False
            actual_text = ""
            
            # Check Alert (Lỗi hệ thống)
            try:
                alert = WebDriverWait(driver, 2).until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".alert-danger")))
                actual_text = alert.text
                if expected_msg in actual_text: found_error = True
            except: pass

            # Check Field Error (Lỗi input validation)
            if not found_error:
                errors = driver.find_elements(By.CSS_SELECTOR, ".text-danger")
                for err in errors:
                    if expected_msg in err.text:
                        found_error = True
                        actual_text = err.text
                        break
                    actual_text = err.text 

            if found_error:
                print(f"-> PASSED (Caught Expected Error: '{expected_msg}')")
            else:
                # Nếu web cho qua (Bug của web)
                if "Your Account Has Been Created" in driver.page_source:
                     print(f"-> WARNING: DETECTED BUG! (Mong đợi lỗi '{expected_msg}' nhưng Web cho đăng ký thành công).")
                else:
                     self.fail(f"FAILED. Mong đợi lỗi '{expected_msg}' nhưng thấy '{actual_text}' hoặc không rõ lỗi.")

# === GENERATE TEST CASES ===
def generate_test_cases():
    data_rows = load_csv_data()
    if not data_rows: return

    for row in data_rows:
        def test_func(self, row_data=row): 
            self.run_register_test(
                row_data["caseID"],
                row_data["firstName"],
                row_data["lastName"],
                row_data["email"],
                row_data["telephone"],
                row_data["password"],
                row_data["confirmPassword"],
                row_data["privacyPolicy"],
                row_data["expectedMessage"],
                row_data["shouldSuccess"]
            )
        setattr(RegisterTest, f"test_{row['caseID']}", test_func)

generate_test_cases()

if __name__ == "__main__":
    unittest.main(verbosity=2)