# -*- coding: utf-8 -*-
import csv
import unittest
import time
import os
import sys

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- CẤU HÌNH ĐƯỜNG DẪN --- data\customerDeposit_lv2.csv
current_dir = os.path.dirname(os.path.abspath(__file__))
CSV_FILE_PATH = os.path.join(current_dir, "../data/customerDeposit_lv2.csv")

def load_csv_data():
    rows = []
    try:
        # Dùng utf-8-sig để tránh lỗi BOM đầu file nếu sửa bằng Excel
        with open(CSV_FILE_PATH, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
    except FileNotFoundError:
        print(f"LỖI: Không tìm thấy file CSV tại: {CSV_FILE_PATH}")
    return rows

class CustomerDepositTest(unittest.TestCase):
    
    def clear_cache(self):
        try:
            self.driver.execute_cdp_cmd("Network.clearBrowserCache", {})
            self.driver.execute_cdp_cmd("Network.clearBrowserCookies", {})
        except:
            pass

    def setUp(self):
        service_obj = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service_obj)
        self.driver.implicitly_wait(10)
        self.driver.maximize_window()
        self.clear_cache()

    def tearDown(self):
        self.driver.quit()

    # Hàm thực thi chính: Nhận toàn bộ dữ liệu từ row (bao gồm cả XPATH)
    def deposit_flow(self, row):
        driver = self.driver
        wait = WebDriverWait(driver, 10)

        # --- TRÍCH XUẤT DỮ LIỆU TỪ CSV ---
        url = row['url']
        username = row['username']
        amount = row['amount']
        expected_message = row['expectedMessage']
        should_increase = row['shouldBalanceIncrease']

        # --- TRÍCH XUẤT LOCATORS (XPATH/ID) TỪ CSV ---
        LOCATOR_BTN_CUSTOMER_LOGIN = row['btnCustomerLoginXPATH']
        LOCATOR_SELECT_USER_ID = row['selectUserID']
        LOCATOR_BTN_LOGIN = row['btnLoginXPATH']
        LOCATOR_TAB_DEPOSIT = row['tabDepositXPATH']
        LOCATOR_LBL_BALANCE = row['lblBalanceXPATH']
        LOCATOR_INPUT_AMOUNT = row['inputAmountXPATH']
        LOCATOR_BTN_SUBMIT = row['btnSubmitXPATH']
        LOCATOR_MSG_ERROR = row['msgErrorXPATH']

        # --- BƯỚC 1: LOGIN ---
        max_retries = 3
        for i in range(max_retries):
            try:
                driver.get(url)
                break # Nếu load thành công thì thoát vòng lặp
            except Exception as e:
                print(f"Lần {i+1}: Mạng lỗi, đang thử lại... {e}")
                time.sleep(2) # Nghỉ 2 giây rồi thử lại
        
        # Click Customer Login
        wait.until(EC.element_to_be_clickable((By.XPATH, LOCATOR_BTN_CUSTOMER_LOGIN))).click()

        # Chọn User (Tìm bằng ID theo file csv cũ của bạn)
        user_select = Select(wait.until(EC.visibility_of_element_located((By.ID, LOCATOR_SELECT_USER_ID))))
        user_select.select_by_visible_text(username)

        # Click Login Button
        wait.until(EC.element_to_be_clickable((By.XPATH, LOCATOR_BTN_LOGIN))).click()

        # Đợi Login thành công (Tên hiện ra)
        wait.until(EC.visibility_of_element_located((By.XPATH, f"//span[contains(text(),'{username}')]")))

        # --- BƯỚC 2: VÀO TAB DEPOSIT ---
        wait.until(EC.element_to_be_clickable((By.XPATH, LOCATOR_TAB_DEPOSIT))).click()

        # --- BƯỚC 3: LẤY SỐ DƯ BAN ĐẦU ---
        # Chờ phần tử số dư load xong
        time.sleep(1) 
        balance_element = driver.find_element(By.XPATH, LOCATOR_LBL_BALANCE)
        initial_balance = int(balance_element.text)

        # --- BƯỚC 4: NHẬP TIỀN VÀ SUBMIT ---
        amount_input = wait.until(EC.visibility_of_element_located((By.XPATH, LOCATOR_INPUT_AMOUNT)))
        amount_input.clear()
        amount_input.send_keys(amount)

        driver.find_element(By.XPATH, LOCATOR_BTN_SUBMIT).click()

        # --- BƯỚC 5: KIỂM TRA KẾT QUẢ ---
        if should_increase == "True":
            # Case hợp lệ: Mong đợi thông báo thành công
            try:
                msg_element = wait.until(EC.visibility_of_element_located((By.XPATH, LOCATOR_MSG_ERROR)))
                self.assertEqual(msg_element.text, expected_message)
            except:
                self.fail(f"Lỗi: Không thấy thông báo '{expected_message}' hiện ra!")
        else:
            # Case không hợp lệ: Kiểm tra số dư không đổi
            time.sleep(1) # Chờ một chút để đảm bảo giao diện đã ổn định
            new_balance = int(driver.find_element(By.XPATH, LOCATOR_LBL_BALANCE).text)
            self.assertEqual(initial_balance, new_balance, "Lỗi: Số dư thay đổi dù input không hợp lệ!")

def generate_test_cases():
    print("Chạy testcase customerDeposit_lv2.py với Full CSV Config")
    data_rows = load_csv_data() 

    if not data_rows:
        return

    for index, row in enumerate(data_rows):
        def test(self, row=row): 
            self.deposit_flow(row)
        
        # Đặt tên test case hiển thị trong log
        test_name = f"test_{row['caseID']}_Amount_{row['amount']}"
        setattr(CustomerDepositTest, test_name, test)

generate_test_cases()

if __name__ == "__main__":
    unittest.main()