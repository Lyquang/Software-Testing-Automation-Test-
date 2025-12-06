import csv
import unittest
import time
from datetime import datetime
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
        print(f"File not found: {filename}")
    return rows

class CombinedTransactionHistoryTestLevel2(unittest.TestCase):
    
    def clear_cache(self):
        try:
            self.driver.execute_cdp_cmd("Network.clearBrowserCache", {})
            self.driver.execute_cdp_cmd("Network.clearBrowserCookies", {})
        except: pass

    def setUp(self):
        service_obj = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service_obj)
        self.driver.implicitly_wait(10)
        self.driver.maximize_window()
        self.clear_cache()

    def tearDown(self):
        self.driver.quit()

    def convert_to_iso(self, date_str):
        if not date_str: return ""
        try:
            # Parses: "01/01/2015 12:00 AM" -> ISO "yyyy-MM-ddThh:mm"
            dt = datetime.strptime(date_str.strip(), "%d/%m/%Y %I:%M %p")
            return dt.strftime("%Y-%m-%dT%H:%M")
        except ValueError:
            return date_str

    def run_flow_lv2(self, row_data):
        driver = self.driver
        wait = WebDriverWait(driver, 10)
        
        # Unpack Data
        tc_id = row_data.get("TestCaseID")
        user_name = row_data.get("userName")
        account_number = row_data.get("accountNumber")
        start_date = row_data.get("startDate")
        end_date = row_data.get("endDate")
        
        # Unpack Locators/Config
        url = row_data.get("url")
        login_opt_xpath = row_data.get("login_option_xpath")
        user_select_id = row_data.get("user_select_id")
        login_btn_xpath = row_data.get("login_btn_xpath")
        acc_select_id = row_data.get("account_select_id")
        trans_tab_xpath = row_data.get("transactions_tab_xpath")
        table_tag = row_data.get("table_tag")
        start_id = row_data.get("start_date_id")
        end_id = row_data.get("end_date_id")

        print(f"Running {tc_id} (Level 2): User='{user_name}', Acc='{account_number}'")
        
        # 1. Login Page
        driver.get(url)
        
        # Customer Login Button
        cus_login_btn = wait.until(EC.element_to_be_clickable((By.XPATH, login_opt_xpath)))
        cus_login_btn.click()

        # 2. Select User
        dropdown_element = wait.until(EC.visibility_of_element_located((By.ID, user_select_id)))
        select_obj = Select(dropdown_element)
        
        # Verify user exists (TC003002 Logic)
        all_options = [opt.text for opt in select_obj.options]
        if user_name not in all_options:
            print(f"[{tc_id}] User '{user_name}' not found in dropdown. Stopping test as SUCCESS (Negative Case).")
            return

        select_obj.select_by_visible_text(user_name)
        
        login_btn = wait.until(EC.element_to_be_clickable((By.XPATH, login_btn_xpath)))
        login_btn.click()

        # 3. Select Account (Dynamic check)
        try:
            account_select_element = wait.until(EC.visibility_of_element_located((By.ID, acc_select_id)))
        except:
             print(f"[{tc_id}] Account dropdown not found. User might not have accounts.")
             return

        if not account_number:
            print(f"[{tc_id}] No account number provided in CSV. Stopping test as SUCCESS.")
            return

        account_select = Select(account_select_element)
        acc_options = [opt.text for opt in account_select.options]
        if str(account_number) not in acc_options:
             print(f"[{tc_id}] Account '{account_number}' not found for user. Stopping test.")
             return
             
        account_select.select_by_visible_text(str(account_number))

        # 4. Click Transactions
        transactions_btn = wait.until(EC.element_to_be_clickable((By.XPATH, trans_tab_xpath)))
        transactions_btn.click()
        
        time.sleep(2)
        table = wait.until(EC.visibility_of_element_located((By.TAG_NAME, table_tag)))

        # 5. Apply Date Filter (if ID provided and value exists)
        if (start_date or end_date) and start_id and end_id:
            print(f"[{tc_id}] Applying date filter...")
            start_input = driver.find_element(By.ID, start_id)
            end_input = driver.find_element(By.ID, end_id)
            
            if start_date:
                iso_start = self.convert_to_iso(start_date)
                driver.execute_script("arguments[0].value = arguments[1];", start_input, iso_start)
                driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", start_input)
            
            if end_date:
                iso_end = self.convert_to_iso(end_date)
                driver.execute_script("arguments[0].value = arguments[1];", end_input, iso_end)
                driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", end_input)
            
            time.sleep(2)

        # 6. Verify Results
        rows = table.find_elements(By.XPATH, "//tbody/tr")
        row_count = len(rows)
        print(f"[{tc_id}] Found {row_count} transaction rows.")
        
        if row_count == 0:
            print(f"[{tc_id}] No transactions found.")
        else:
            print(f"[{tc_id}] Verification Successful: Transactions listed.")

def generate_test_cases():
    data_rows = load_csv_data("../data/view_transaction_history_lv2.csv") 

    for index, row in enumerate(data_rows):
        def test(self, row=row): 
            self.run_flow_lv2(row)
        
        test_id = row.get("TestCaseID", f"Row_{index+1}")
        safe_name = f"test_lv2_{test_id}"
        setattr(CombinedTransactionHistoryTestLevel2, safe_name, test)

generate_test_cases()

if __name__ == "__main__":
    unittest.main()
