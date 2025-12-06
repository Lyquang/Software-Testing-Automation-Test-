# -*- coding: utf-8 -*-
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

# --- CẤU HÌNH ĐƯỜNG DẪN ---
current_dir = os.path.dirname(os.path.abspath(__file__))
# Đổi tên file env tương ứng với chức năng Deposit
env_path = os.path.join(current_dir, 'customerDeposit.env')

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

class CustomerDepositTest(unittest.TestCase):
    
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
        # Lấy tài khoản test mặc định từ env để login trước khi deposit
        self.default_user = os.getenv("DEFAULT_TEST_USER") 

    def tearDown(self):
        self.driver.quit()

    # Hàm phụ trợ: Login nhanh để vào màn hình Deposit
    def perform_login(self):
        driver = self.driver
        wait = WebDriverWait(driver, 10)
        driver.get(self.base_url)

        # 1. Click Customer Login
        cus_login_xpath = os.getenv("LOCATOR_BTN_CUSTOMER_LOGIN_XPATH")
        wait.until(EC.element_to_be_clickable((By.XPATH, cus_login_xpath))).click()

        # 2. Chọn User
        user_select_id = os.getenv("LOCATOR_SELECT_USER_ID")
        user_select = Select(wait.until(EC.visibility_of_element_located((By.ID, user_select_id))))
        user_select.select_by_visible_text(self.default_user)

        # 3. Click Login
        login_btn_xpath = os.getenv("LOCATOR_BTN_LOGIN_XPATH")
        wait.until(EC.element_to_be_clickable((By.XPATH, login_btn_xpath))).click()

        # 4. Đợi tên hiện ra để chắc chắn đã login
        wait.until(EC.visibility_of_element_located((By.XPATH, f"//span[contains(text(),'{self.default_user}')]")))

    def deposit_flow(self, amount, expected_message, should_increase):
        driver = self.driver
        wait = WebDriverWait(driver, 10)

        # BƯỚC 1: Đăng nhập trước
        self.perform_login()

        # BƯỚC 2: Chuyển qua tab Deposit
        tab_deposit_xpath = os.getenv("LOCATOR_TAB_DEPOSIT_XPATH")
        wait.until(EC.element_to_be_clickable((By.XPATH, tab_deposit_xpath))).click()

        # BƯỚC 3: Lấy số dư ban đầu
        lbl_balance_xpath = os.getenv("LOCATOR_LBL_BALANCE_XPATH")
        # Chờ một chút để số dư load xong
        time.sleep(1) 
        balance_element = driver.find_element(By.XPATH, lbl_balance_xpath)
        initial_balance = int(balance_element.text)

        # BƯỚC 4: Nhập tiền và Submit
        input_amount_xpath = os.getenv("LOCATOR_INPUT_AMOUNT_XPATH")
        amount_input = wait.until(EC.visibility_of_element_located((By.XPATH, input_amount_xpath)))
        amount_input.clear()
        amount_input.send_keys(amount)

        btn_submit_xpath = os.getenv("LOCATOR_BTN_SUBMIT_XPATH")
        driver.find_element(By.XPATH, btn_submit_xpath).click()

        # BƯỚC 5: Kiểm tra kết quả
        if should_increase == "True":
            # Case hợp lệ: Mong đợi thông báo thành công
            msg_xpath = os.getenv("LOCATOR_MSG_ERROR_XPATH") # Dùng chung xpath hiển thị msg
            try:
                msg_element = wait.until(EC.visibility_of_element_located((By.XPATH, msg_xpath)))
                self.assertEqual(msg_element.text, expected_message)
            except:
                self.fail("Lỗi: Không thấy thông báo thành công hiện ra!")
        else:
            # Case không hợp lệ (vd: nhập chữ, số âm... tùy logic web)
            # Ở web này nếu nhập sai nó không hiện gì hoặc không đổi tiền, ta check số dư
            time.sleep(1)
            new_balance = int(driver.find_element(By.XPATH, lbl_balance_xpath).text)
            self.assertEqual(initial_balance, new_balance, "Lỗi: Số dư thay đổi dù input không hợp lệ!")

def generate_test_cases():
    csv_filename = os.getenv("CSV_FILE")
    
    if not csv_filename:
        return

    data_rows = load_csv_data(csv_filename) 

    for index, row in enumerate(data_rows):
        def test(self, row=row): 
            self.deposit_flow(
                row["amount"],
                row["expectedMessage"],
                row["shouldBalanceIncrease"]
            )
        
        test_name = f"test_deposit_{index+1}_amount_{row['amount']}"
        setattr(CustomerDepositTest, test_name, test)

generate_test_cases()

if __name__ == "__main__":
    unittest.main()