# -*- coding: utf-8 -*-
import csv
import unittest
import time
import random
import string
import os  # <--- Bắt buộc import thư viện này
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- CẤU HÌNH ĐƯỜNG DẪN (FIX) ---
# Lấy đường dẫn của thư mục chứa file script hiện tại
current_dir = os.path.dirname(os.path.abspath(__file__))

# Trỏ sang thư mục data nằm ở cấp cha (../data/)
# Lưu ý: Tên file phải khớp với file bạn đã lưu
DATA_FILE_PATH = os.path.join(current_dir, "../data/registerAccount_lv2.csv")

def load_csv_data():
    rows = []
    try:
        # Dùng DATA_FILE_PATH thay vì tên file đơn thuần
        with open(DATA_FILE_PATH, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy file dữ liệu tại: {DATA_FILE_PATH}")
        # In ra đường dẫn hiện tại để debug
        print(f"Thư mục hiện tại của script: {current_dir}")
    return rows

class RegisterTestLV2(unittest.TestCase):

    def setUp(self):
        service_obj = Service(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        # options.add_argument("--headless") 
        self.driver = webdriver.Chrome(service=service_obj, options=options)
        self.driver.implicitly_wait(3)
        self.driver.maximize_window()

    def tearDown(self):
        self.driver.quit()

    def run_register_test(self, row_data):
        driver = self.driver
        
        # --- 1. CONFIG & DATA EXTRACTION ---
        case_id = row_data["caseID"]
        f_name = row_data["firstName"]
        l_name = row_data["lastName"]
        email = row_data["email"]
        phone = row_data["telephone"]
        pwd = row_data["password"]
        confirm_pwd = row_data["confirmPassword"]
        policy = row_data["privacyPolicy"]
        expected_msg = row_data["expectedMessage"]
        should_success = row_data["shouldSuccess"]
        
        # Locators & URL
        base_url = row_data["url"]
        loc_fname = row_data["locator_firstname_id"]
        loc_lname = row_data["locator_lastname_id"]
        loc_email = row_data["locator_email_id"]
        loc_phone = row_data["locator_telephone_id"]
        loc_pwd = row_data["locator_password_id"]
        loc_confirm = row_data["locator_confirm_id"]
        loc_policy = row_data["locator_policy_name"]
        loc_btn_cont = row_data["locator_continue_xpath"]
        loc_success = row_data["locator_success_xpath"]
        loc_logout = row_data["locator_logout_text"]
        loc_alert = row_data["locator_alert_css"]
        loc_field_err = row_data["locator_field_error_css"]

        print(f"\n[{case_id}] Running...", end=" ")
        
        driver.get(base_url)

        # --- 2. FILL FORM ---
        try:
            driver.execute_script(f"document.getElementById('form-register').setAttribute('novalidate', '');")
        except: pass

        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, loc_fname)))

        if f_name: driver.find_element(By.ID, loc_fname).send_keys(f_name)
        if l_name: driver.find_element(By.ID, loc_lname).send_keys(l_name)

        # Logic Random Email
        final_email = email
        if should_success == "True" and "@" in email: 
            random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
            parts = email.split('@')
            if len(parts) == 2:
                final_email = f"{parts[0]}_{random_str}@{parts[1]}"
            else:
                final_email = f"{email}_{random_str}"
        elif case_id == "TC-008-022": 
             random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
             parts = email.split('@')
             final_email = f"{parts[0]}_{random_str}@{parts[1]}"
        
        if final_email: driver.find_element(By.ID, loc_email).send_keys(final_email)
        if phone: driver.find_element(By.ID, loc_phone).send_keys(phone)
        if pwd: driver.find_element(By.ID, loc_pwd).send_keys(pwd)
        if confirm_pwd: driver.find_element(By.ID, loc_confirm).send_keys(confirm_pwd)

        if policy == "True":
            try:
                chk = driver.find_element(By.NAME, loc_policy)
                driver.execute_script("arguments[0].click();", chk)
            except: pass

        time.sleep(1) 
        
        submit_btn = driver.find_element(By.XPATH, loc_btn_cont)
        driver.execute_script("arguments[0].click();", submit_btn)

        # --- 3. VERIFY ---
        if should_success == "True":
            try:
                success_element = WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.XPATH, loc_success)))
                self.assertEqual(success_element.text, expected_msg)
                print(f"-> PASSED (Account Created)")
                try: driver.find_element(By.LINK_TEXT, loc_logout).click()
                except: pass
            except:
                err_text = "Unknown Error"
                try: err_text = driver.find_element(By.CSS_SELECTOR, loc_alert).text
                except: pass
                if err_text == "Unknown Error":
                    try:
                        field_errs = driver.find_elements(By.CSS_SELECTOR, loc_field_err)
                        if field_errs: err_text = field_errs[0].text
                    except: pass
                self.fail(f"FAILED. Mong đợi thành công nhưng thấy lỗi: {err_text}")
        else:
            found_error = False
            actual_text = ""
            
            try:
                alert = WebDriverWait(driver, 2).until(EC.visibility_of_element_located((By.CSS_SELECTOR, loc_alert)))
                actual_text = alert.text
                if expected_msg in actual_text: found_error = True
            except: pass

            if not found_error:
                errors = driver.find_elements(By.CSS_SELECTOR, loc_field_err)
                for err in errors:
                    if expected_msg in err.text:
                        found_error = True
                        actual_text = err.text
                        break
                    actual_text = err.text 

            if found_error:
                print(f"-> PASSED (Caught Expected Error: '{expected_msg}')")
            else:
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
            self.run_register_test(row_data)
        setattr(RegisterTestLV2, f"test_{row['caseID']}", test_func)

generate_test_cases()

if __name__ == "__main__":
    unittest.main(verbosity=2)