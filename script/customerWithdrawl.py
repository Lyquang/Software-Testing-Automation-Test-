# -*- coding: utf-8 -*-
import csv
import unittest
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager

def load_csv_data():
    rows = []
    try:
        with open("../data/customerWithdrawl.csv", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
    except FileNotFoundError:
        print("Lỗi: Không tìm thấy file customerWithdrawl.csv")
    return rows

class WithdrawTest(unittest.TestCase):

    def setUp(self):
        # Cấu hình Driver
        service_obj = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service_obj)
        self.driver.implicitly_wait(10)
        self.driver.maximize_window()
        self.base_url = "https://www.globalsqa.com/angularJs-protractor/BankingProject/#/login"

    def tearDown(self):
        self.driver.quit()

    # 1. Login
    def login_as_customer(self, customer_name="Harry Potter"):
        driver = self.driver
        driver.get(self.base_url)
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Customer Login')]"))).click()
        user_select = Select(WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "userSelect"))))
        user_select.select_by_visible_text(customer_name)
        driver.find_element(By.XPATH, "//button[text()='Login']").click()
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, f"//span[contains(text(),'{customer_name}')]")))

    # 2. Hàm nạp tiền (Để tạo dữ liệu mẫu trước khi rút)
    def deposit_money(self, amount):
        driver = self.driver
        driver.find_element(By.XPATH, "//button[contains(text(),'Deposit')]").click()
        
        amount_input = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//input[@ng-model='amount']")))
        amount_input.clear()
        amount_input.send_keys(amount)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        # Chờ xác nhận nạp xong
        WebDriverWait(driver, 5).until(EC.text_to_be_present_in_element((By.XPATH, "//span[@ng-show='message']"), "Deposit Successful"))
        time.sleep(1) # Chờ số dư cập nhật

    # 3. Logic chính: Test Rút tiền
    def run_withdraw_test(self, initial_balance, withdraw_amount, expected_msg, expect_success):
        driver = self.driver
        
        # Bước A: Login và Nạp tiền làm vốn (Precondition)
        self.login_as_customer("Harry Potter")
        self.deposit_money(initial_balance)
        
        # Bước B: Chuyển sang Tab Withdraw
        # Lưu ý: Trên web này nút Withdraw viết sai chính tả là "Withdrawl" hoặc có khoảng trắng
        withdraw_tab = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Withdraw')]")))
        withdraw_tab.click()
        
        # Lấy số dư trước khi rút để so sánh
        time.sleep(1)
        old_balance = int(driver.find_element(By.XPATH, "//strong[2]").text)

        # Bước C: Nhập số tiền muốn rút
        # Lưu ý: XPath ô nhập của Withdraw hơi khác Deposit một chút
        amount_input = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//input[@ng-model='amount']")))
        amount_input.clear()
        amount_input.send_keys(withdraw_amount)
        
        # Bước D: Bấm nút Rút
        submit_btn = driver.find_element(By.XPATH, "//button[@type='submit']")
        submit_btn.click()
        
        time.sleep(1) # Chờ hệ thống xử lý

        # Bước E: Kiểm tra kết quả (Verification)
        message_element = driver.find_element(By.XPATH, "//span[@ng-show='message']")
        actual_msg = message_element.text
        
        # Lấy số dư mới
        new_balance = int(driver.find_element(By.XPATH, "//strong[2]").text)

        print(f"--- Test Case: Rút {withdraw_amount} từ {initial_balance} ---")
        print(f"Thông báo thực tế: {actual_msg}")

        # Kiểm tra nội dung thông báo
        if expected_msg:
             self.assertIn(expected_msg, actual_msg, f"Sai thông báo! Mong đợi chứa: '{expected_msg}', Thực tế: '{actual_msg}'")

        # Kiểm tra logic số dư
        if expect_success == "True":
            expected_balance = int(initial_balance) - int(withdraw_amount)
            self.assertEqual(new_balance, expected_balance, f"Lỗi số dư! Cũ: {old_balance}, Rút: {withdraw_amount}. Mong đợi: {expected_balance}, Thực tế: {new_balance}")
            print("=> KẾT QUẢ: PASS (Rút thành công, số dư trừ đúng)")
        else:
            self.assertEqual(new_balance, int(initial_balance), "Lỗi: Rút thất bại nhưng số dư lại bị thay đổi!")
            print("=> KẾT QUẢ: PASS (Rút thất bại đúng như mong đợi, số dư giữ nguyên)")

        # Dừng 3 giây để bạn kịp nhìn màn hình
        time.sleep(3)

# === TỰ ĐỘNG GEN TEST CASE ===
def generate_test_cases():
    data_rows = load_csv_data()
    if not data_rows: return

    for index, row in enumerate(data_rows):
        def test(self, row=row): 
            self.run_withdraw_test(
                row["initialBalance"],
                row["withdrawAmount"],
                row["expectedMessage"],
                row["expectSuccess"]
            )
        test_name = f"test_{row['caseID']}_Withdraw_{row['withdrawAmount']}"
        setattr(WithdrawTest, test_name, test)

generate_test_cases()

if __name__ == "__main__":
    unittest.main()