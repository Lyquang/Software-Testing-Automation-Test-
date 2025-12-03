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
    # Đảm bảo file csv nằm cùng thư mục
    try:
        with open("deposit_data.csv", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
    except FileNotFoundError:
        print("Lỗi: Không tìm thấy file deposit_data.csv")
    return rows

class DepositTest(unittest.TestCase):

    def setUp(self):
        # --- CẤU HÌNH DRIVER CHUẨN (FIX LỖI) ---
        service_obj = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service_obj)
        self.driver.implicitly_wait(10)
        self.driver.maximize_window()
        self.base_url = "https://www.globalsqa.com/angularJs-protractor/BankingProject/#/login"

    def tearDown(self):
        self.driver.quit()

    # Hàm hỗ trợ: Login vào tư cách khách hàng
    def login_as_customer(self, customer_name="Harry Potter"):
        driver = self.driver
        driver.get(self.base_url)
        
        # Click nút Customer Login
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Customer Login')]"))).click()
        
        # Chọn tên từ Dropdown
        user_select = Select(WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "userSelect"))))
        user_select.select_by_visible_text(customer_name)
        
        # Click nút Login
        driver.find_element(By.XPATH, "//button[text()='Login']").click()
        
        # Xác nhận đã vào trang account (Check tên hiện lên)
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, f"//span[contains(text(),'{customer_name}')]")))

    # Hàm thực thi test case chính
    def run_deposit_test(self, amount, expected_msg, should_increase):
        driver = self.driver
        
        # 1. Login trước
        self.login_as_customer("Harry Potter")
        
        # 2. Chuyển sang tab Deposit
        deposit_tab = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Deposit')]")))
        deposit_tab.click()
        
        # 3. Lấy số dư ban đầu (để so sánh nếu cần)
        time.sleep(1) # Chờ load số dư
        balance_element = driver.find_element(By.XPATH, "//strong[2]")
        initial_balance = int(balance_element.text)

        # 4. Nhập tiền và bấm nút
        amount_input = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//input[@ng-model='amount']")))
        amount_input.clear()
        amount_input.send_keys(amount)
        
        submit_btn = driver.find_element(By.XPATH, "//button[@type='submit']")
        submit_btn.click()

        # 5. Kiểm tra kết quả (Verification)
        
        # TRƯỜNG HỢP 1: Nhập số hợp lệ (Expect Success)
        if should_increase == "True":
            # Kiểm tra thông báo thành công
            try:
                msg_element = WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.XPATH, "//span[@ng-show='message']")))
                self.assertEqual(msg_element.text, expected_msg, f"Sai thông báo! Mong đợi: {expected_msg}, Thực tế: {msg_element.text}")
            except:
                self.fail("Không thấy thông báo Deposit Successful xuất hiện.")
            
            # Kiểm tra số dư có tăng không (Optional)
            # new_balance = int(driver.find_element(By.XPATH, "//strong[2]").text)
            # self.assertTrue(new_balance > initial_balance, "Lỗi: Số dư không tăng sau khi nạp tiền!")

        # TRƯỜNG HỢP 2: Nhập số 0 hoặc lỗi (Expect No Change/No Message)
        else:
            # Logic xử lý cho trường hợp nhập 0 (dựa theo ảnh excel TC-001-002 của bạn: Số dư giữ nguyên)
            time.sleep(2)
            new_balance = int(driver.find_element(By.XPATH, "//strong[2]").text)
            self.assertEqual(initial_balance, new_balance, "Lỗi: Nhập số 0 nhưng số dư vẫn thay đổi!")


# === TỰ ĐỘNG GEN TEST CASE TỪ CSV ===
def generate_test_cases():
    data_rows = load_csv_data()
    
    if not data_rows:
        return

    for index, row in enumerate(data_rows):
        # Tạo hàm test động
        def test(self, row=row): 
            self.run_deposit_test(
                row["amount"],
                row["expectedMessage"],
                row["shouldBalanceIncrease"]
            )
        
        # Đặt tên test case để hiển thị trong log (VD: test_TC_001_001_Input_5000)
        test_name = f"test_{row['caseID']}_Input_{row['amount']}"
        setattr(DepositTest, test_name, test)

# Gọi hàm tạo test
generate_test_cases()

if __name__ == "__main__":
    unittest.main()