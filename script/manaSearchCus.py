# -*- coding: utf-8 -*-
import csv
import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import NoAlertPresentException
import unittest, time, re
import csv
from pathlib import Path

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


from selenium.webdriver.chrome.service import Service

def load_csv_data():
    rows = []
    with open("../data/manaSearchCusData.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows

class BaseTest(unittest.TestCase):


    def add_customer(self, firstName, lastName, postCode):
        driver = self.driver

        driver.get("https://www.globalsqa.com/angularJs-protractor/BankingProject/#/manager/addCust")
        first_name_input = driver.find_element(By.XPATH, "//input[@ng-model='fName']")
        last_name_input = driver.find_element(By.XPATH, "//input[@ng-model='lName']")
        post_code_input = driver.find_element(By.XPATH, "//input[@ng-model='postCd']")
        add_customer_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        first_name_input.clear()
        first_name_input.send_keys(firstName)
        
        last_name_input.clear()
        last_name_input.send_keys(lastName)
        
        post_code_input.clear()
        post_code_input.send_keys(postCode)
        
        add_customer_button.click()
        
        WebDriverWait(driver, 5).until(EC.alert_is_present())
        alert = driver.switch_to.alert
        alert_text = alert.text
        self.assertIn("Customer added successfully with customer id", alert_text) 
        alert.accept()
        
        driver.get("https://www.globalsqa.com/angularJs-protractor/BankingProject/#/manager/list")
    
    def clear_cache(self):
        self.driver.execute_cdp_cmd("Network.clearBrowserCache", {})
        self.driver.execute_cdp_cmd("Network.clearBrowserCookies", {})

    # def setUp(self):
    #     self.driver = webdriver.Chrome(ChromeDriverManager().install())
    #     self.driver.implicitly_wait(30)
    #     self.base_url = "https://www.google.com/"
    #     self.verificationErrors = []
    #     self.accept_next_alert = True
    
    def setUp(self):
        # SỬA LỖI TẠI ĐÂY:
        # Bọc ChromeDriverManager().install() vào trong Service()
        service_obj = Service(ChromeDriverManager().install())
        
        # Truyền service vào webdriver.Chrome
        self.driver = webdriver.Chrome(service=service_obj)
        
        self.driver.implicitly_wait(30)
        self.base_url = "https://www.google.com/"
        self.verificationErrors = []
        self.accept_next_alert = True
        

    def tearDown(self):
        self.driver.quit()

    def run_test_case(self, expectRow, inputSearch,  expectFirstName, expectLastName,checkName):
        driver = self.driver
        self.clear_cache()
        self.add_customer("Tom", "Weasly", "POI294")
        driver.get("https://www.globalsqa.com/angularJs-protractor/BankingProject/#/manager/list")
        driver.refresh()
        search_box = driver.find_element(By.XPATH, "//input[@type='text']")
        search_box.clear()
        search_box.send_keys(inputSearch)
        wait = WebDriverWait(driver, 10) # Chờ tối đa 10 giây
        
        expected_rows = int(expectRow)
        if expected_rows > 0:
            row_xpath = f"//tbody/tr[{expected_rows}]"
            try:
                wait.until(EC.presence_of_element_located((By.XPATH, row_xpath)))
            except:
                self.fail(f"Expected {expected_rows} row(s) but the last expected row was not found.")
        time.sleep(1)
        i=0
        for i in range(1, int(expectRow) + 1):
            self.assertTrue(self.is_element_present(By.XPATH, "//tbody/tr[" + str(i) + "]"))
            
        if inputSearch !="":
            self.assertFalse(self.is_element_present(By.XPATH, "//tbody/tr[" + str(i+1) + "]"))

        if checkName == '1':
            first_name_cell = driver.find_element(By.XPATH, "//tbody/tr[1]/td[1]")
            self.assertEqual(expectFirstName, first_name_cell.text)
            last_name_cell = driver.find_element(By.XPATH, "//tbody/tr[1]/td[2]")
            self.assertEqual(expectLastName, last_name_cell.text)

    def is_element_present(self, how, what):
        try:
            self.driver.find_element(how, what)
            return True
        except:
            return False


# === TỰ ĐỘNG TẠO TEST CASE TỪ CSV ===
def generate_test_cases():
    data_rows = load_csv_data()

    for index, row in enumerate(data_rows):

        def test(self, row=row): 
            self.run_test_case(
                row["expectRow"],
                row["inputSearch"],
                row["expectFirstName"],
                row["expectLastName"],
                row["checkName"],
                )

        test_name = f"test_customer_search_{index+1}_{row['inputSearch']}"
        setattr(BaseTest, test_name, test)


generate_test_cases()


if __name__ == "__main__":
    unittest.main()
