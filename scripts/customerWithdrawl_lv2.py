# -*- coding: utf-8 -*-
import csv
import unittest
import time
import os

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager

# --- CẤU HÌNH ĐƯỜNG DẪN TỰ ĐỘNG ---
current_dir = os.path.dirname(os.path.abspath(__file__))
CSV_FILE_PATH = os.path.join(current_dir, "../data/customerWithdrawl_lv2.csv")

def load_csv_data():
    rows = []
    try:
        # Dùng utf-8-sig để xử lý BOM nếu file được sửa bằng Excel
        with open(CSV_FILE_PATH, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
    except FileNotFoundError:
        print(f"LỖI: Không tìm thấy file CSV tại: {CSV_FILE_PATH}")
    return rows

class WithdrawTest(unittest.TestCase):

    def setUp(self):
        service_obj = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service_obj)
        self.driver.implicitly_wait(10)
        self.driver.maximize_window()
        
        # --- QUAN TRỌNG: Clear Cache/Storage để reset trạng thái (số dư về 0) ---
        # Chúng ta cần load 1 trang bất kỳ trước khi clear storage
        self.driver.get("https://www.google.com") 
        try:
            self.driver.execute_script("window.localStorage.clear();")
            self.driver.execute_script("window.sessionStorage.clear();")
            self.driver.delete_all_cookies()
        except:
            pass

    def tearDown(self):
        self.driver.quit()

    # Hàm thực thi chính: Nhận toàn bộ 'row' từ CSV
    def run_withdraw_test(self, row):
        driver = self.driver
        wait = WebDriverWait(driver, 10)

        # --- 1. TRÍCH XUẤT DỮ LIỆU & LOCATORS TỪ CSV ---
        # Data
        url = row['url']
        user_name = row['customerName']
        initial_balance = row['initialBalance']
        withdraw_amount = row['withdrawAmount']
        expected_msg = row['expectedMessage']
        expect_success = str(row['expectSuccess']).lower() == "true"

        # Locators (XPATH)
        BTN_CUS_LOGIN = row['btnCustomerLoginXPATH']
        SELECT_USER = row['selectUserID']
        BTN_LOGIN = row['btnLoginXPATH']
        TAB_DEPOSIT = row['tabDepositXPATH']
        TAB_WITHDRAW = row['tabWithdrawXPATH']
        INPUT_AMOUNT = row['inputAmountXPATH']
        BTN_SUBMIT = row['btnSubmitXPATH']
        MSG_ERROR = row['msgErrorXPATH']
        LBL_BALANCE = row['lblBalanceXPATH']

        # --- 2. LOGIN (Precondition) ---
        driver.get(url)
        wait.until(EC.element_to_be_clickable((By.XPATH, BTN_CUS_LOGIN))).click()
        
        user_select = Select(wait.until(EC.visibility_of_element_located((By.ID, SELECT_USER))))
        user_select.select_by_visible_text(user_name)
        
        wait.until(EC.element_to_be_clickable((By.XPATH, BTN_LOGIN))).click()
        # Chờ tên user hiện ra để xác nhận login
        wait.until(EC.visibility_of_element_located((By.XPATH, f"//span[contains(text(),'{user_name}')]")))

        # --- 3. NẠP TIỀN (Precondition: Tạo vốn để rút) ---
        wait.until(EC.element_to_be_clickable((By.XPATH, TAB_DEPOSIT))).click()
        
        # Nhập tiền nạp
        inp = wait.until(EC.visibility_of_element_located((By.XPATH, INPUT_AMOUNT)))
        inp.clear()
        inp.send_keys(initial_balance)
        
        driver.find_element(By.XPATH, BTN_SUBMIT).click()
        # Chờ thông báo nạp thành công
        wait.until(EC.text_to_be_present_in_element((By.XPATH, MSG_ERROR), "Deposit Successful"))

        # --- 4. RÚT TIỀN (Test Action) ---
        wait.until(EC.element_to_be_clickable((By.XPATH, TAB_WITHDRAW))).click()
        time.sleep(1) # Chờ chuyển tab và load số dư

        # Lấy số dư TRƯỚC khi rút
        balance_element = driver.find_element(By.XPATH, LBL_BALANCE)
        balance_before = int(balance_element.text)

        # Nhập tiền rút
        # Lưu ý: Tìm lại element input để tránh StaleElementReferenceException
        inp_withdraw = wait.until(EC.visibility_of_element_located((By.XPATH, INPUT_AMOUNT)))
        inp_withdraw.clear()
        inp_withdraw.send_keys(withdraw_amount)

        # Click Rút (Tìm lại nút submit để đảm bảo nút mới nhất)
        btn_withdraw = wait.until(EC.element_to_be_clickable((By.XPATH, BTN_SUBMIT)))
        btn_withdraw.click()

        # --- 5. LẤY KẾT QUẢ (Verification) ---
        
        # Xử lý Message (Có thể rỗng nếu nhập 0đ)
        actual_msg = ""
        try:
            # Chờ tối đa 3s xem có chữ nào hiện lên không
            WebDriverWait(driver, 3).until(
                lambda d: d.find_element(By.XPATH, MSG_ERROR).text.strip() != ""
            )
            actual_msg = driver.find_element(By.XPATH, MSG_ERROR).text
        except:
            actual_msg = "" # Timeout, coi như không có thông báo

        # Lấy số dư SAU khi rút
        balance_after = int(driver.find_element(By.XPATH, LBL_BALANCE).text)

        print(f"--- Case: Rút {withdraw_amount} | Msg: '{actual_msg}' | Balance: {balance_before} -> {balance_after}")

        # --- 6. SO SÁNH (ASSERTION) ---
        
        # A. Kiểm tra Message (Không phân biệt hoa thường)
        if expected_msg:
            self.assertIn(expected_msg.lower(), actual_msg.lower(), 
                          f"Sai thông báo! Mong đợi: '{expected_msg}', Thực tế: '{actual_msg}'")

        # B. Kiểm tra Số dư
        if expect_success:
            expected_bal = balance_before - int(withdraw_amount)
            self.assertEqual(balance_after, expected_bal, 
                             f"Sai số dư (Thành công)! Trước: {balance_before}, Rút: {withdraw_amount}. Mong đợi: {expected_bal}, Thực tế: {balance_after}")
        else:
            self.assertEqual(balance_after, balance_before, 
                             f"Sai số dư (Thất bại)! Rút thất bại nhưng tiền vẫn bị trừ. Trước: {balance_before}, Sau: {balance_after}")

def generate_test_cases():
    print("Chạy testcase customerWithdrawl_lv2.py với Full CSV Config")
    data_rows = load_csv_data()
    if not data_rows: return

    for index, row in enumerate(data_rows):
        def test(self, row=row): 
            self.run_withdraw_test(row)
        
        test_name = f"test_{row['caseID']}_Withdraw_{row['withdrawAmount']}"
        setattr(WithdrawTest, test_name, test)

generate_test_cases()

if __name__ == "__main__":
    unittest.main()