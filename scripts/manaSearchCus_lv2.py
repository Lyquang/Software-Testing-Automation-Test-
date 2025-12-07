import csv
import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service # <--- THÊM DÒNG NÀY

def load_csv_data():
    rows = []
    with open("../data/manaSearchCusData_lv2.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


class BaseTest(unittest.TestCase):

    def clear_cache(self):
        self.driver.execute_cdp_cmd("Network.clearBrowserCache", {})
        self.driver.execute_cdp_cmd("Network.clearBrowserCookies", {})

    def setUp(self):
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service)
        self.driver.implicitly_wait(20)
        self.verificationErrors = []

    def tearDown(self):
        if hasattr(self, 'driver') and self.driver:
            self.driver.quit()

        if self.verificationErrors:
            self.fail("\n".join(self.verificationErrors))

    def add_customer(self, firstName, lastName, postCode, addCusURL,fname_XPATH, lname_XPATH, postCode_XPATH, btnSubmit_XPATH):
        
        fnameXPATH =fname_XPATH
        lnameXPATH =lname_XPATH
        postCodeXPATH =postCode_XPATH
        btnSubmitXPATH =btnSubmit_XPATH
        driver = self.driver
        driver.get(addCusURL)

        try:
            driver.find_element(By.XPATH, fnameXPATH).send_keys(firstName)
            driver.find_element(By.XPATH, lnameXPATH).send_keys(lastName)
            driver.find_element(By.XPATH, postCodeXPATH).send_keys(postCode)

            driver.find_element(By.XPATH, btnSubmitXPATH).click()
            WebDriverWait(driver, 5).until(EC.alert_is_present())
            alert = driver.switch_to.alert

            self.assertIn("Customer added successfully with customer id", alert.text)
            alert.accept()

        except AssertionError as e:
            self.verificationErrors.append(f"Lỗi xác minh alert thêm mới: {e}")
        except NoSuchElementException:
            self.verificationErrors.append("Không tìm thấy input hoặc button Add Customer.")

    def run_test_case(self, fNameAddCus, lNameAddCus, codeAddCus, addCusURL,fname_XPATH,lname_XPATH,postCode_XPATH,btnSubmit_XPATH, expectRow, inputSearch, expectFirstName, expectLastName, searchCusURL, searchBox_XPATH, row1_XPATH, row2_XPATH, check_flag):

        searchBoxXPATH = searchBox_XPATH
        row1XPATH = row1_XPATH
        row2XPATH = row2_XPATH

        driver = self.driver
        self.clear_cache()

        self.add_customer(fNameAddCus, lNameAddCus, codeAddCus, addCusURL, fname_XPATH, lname_XPATH, postCode_XPATH, btnSubmit_XPATH)

        driver.get(searchCusURL)
        driver.refresh()

        
        
        try:
            search_box = driver.find_element(By.XPATH, searchBoxXPATH)
            search_box.clear()
            search_box.send_keys(inputSearch)
        except:
            self.verificationErrors.append("Không tìm thấy ô search!")
            return

        time.sleep(1)
        total_expect = int(expectRow)

        for i in range(1, total_expect + 1):
            if not self.is_element_present(By.XPATH, f"//tbody/tr[{i}]"):
                self.verificationErrors.append(f"Thiếu row thứ {i} nhưng kỳ vọng phải có.")
        
        if inputSearch != "":
            if self.is_element_present(By.XPATH, f"//tbody/tr[{total_expect+1}]"):
                self.verificationErrors.append(f"Xuất hiện nhiều hơn {total_expect} row!")

        if check_flag and total_expect > 0:
            try:
                first = driver.find_element(By.XPATH, row1XPATH).text
                last = driver.find_element(By.XPATH, row2XPATH).text

                self.assertEqual(expectFirstName, first)
                self.assertEqual(expectLastName, last)

            except AssertionError as e:
                self.verificationErrors.append(str(e))
            except:
                self.verificationErrors.append("Không tìm thấy cột tên customer.")

    def is_element_present(self, how, what):
        try:
            self.driver.find_element(how, what)
            return True
        except:
            return False


def generate_test_cases():
    data_rows = load_csv_data()

    for index, row in enumerate(data_rows):
        def test(self, row=row):
            check_flag = row["checkName"] == "1"
            self.run_test_case(
                row["fNameAddCus"],
                row["lNameAddCus"],
                row["codeAddCus"],
                row["addCusURL"],
                row["fnameXPATH"],
                row["lnameXPATH"],
                row["postCodeXPATH"],
                row["btnSubmitXPATH"],
                row["expectRow"],
                row["inputSearch"],
                row["expectFirstName"],
                row["expectLastName"],
                row["searchCusURL"],
                row["searchBoxXPATH"],
                row["row1XPATH"],
                row["row2XPATH"],
                check_flag
            )

        test_name = f"test_search_case_{index+1}_{row['inputSearch']}"
        setattr(BaseTest, test_name, test)


generate_test_cases()

if __name__ == "__main__":
    unittest.main()
