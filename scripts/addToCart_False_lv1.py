import csv
import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import unittest, time, re
import csv
from pathlib import Path
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def load_csv_data():
    rows = []
    with open("../data/addToCart_False_lv1.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows

class BaseTest(unittest.TestCase):

    
    def clear_cache(self):
        self.driver.execute_cdp_cmd("Network.clearBrowserCache", {})
        self.driver.execute_cdp_cmd("Network.clearBrowserCookies", {})

    def setUp(self):
        self.driver = webdriver.Chrome(ChromeDriverManager().install())
        self.driver.implicitly_wait(30)
        self.base_url = "https://www.google.com/"
        self.driver.maximize_window()
        self.verificationErrors = []
        self.accept_next_alert = True
        

    def tearDown(self):
        if hasattr(self, 'driver') and self.driver:
            self.driver.quit()
        if self.verificationErrors:
            self.fail("\n".join(self.verificationErrors))
            
    def run_test_case(self, itemsInCartBeforeExpect, numberItemsExpect, textSuccessExpect, itemsInCartAfterExpect):
        driver = self.driver
        wait = WebDriverWait(driver, 10) 
        
        CART_COUNT_XPATH = "//div[@id='entry_217825']/a/div/span"
        QUANTITY_INPUT_XPATH = "//div[@id='entry_216841']/div/input"
        ADD_TO_CART_BUTTON_XPATH = "//div[@id='entry_216842']/button"
        SUCCESS_MESSAGE_XPATH = "//div[@id='notification-box-top']/div/div[2]/div/p"
        
        self.clear_cache()
        driver.get(f"https://ecommerce-playground.lambdatest.io/index.php?route=product/product&product_id=60")
        driver.refresh()
        
        try: 
            itemsInCart_before = driver.find_element(By.XPATH, CART_COUNT_XPATH).text
            self.assertEqual(itemsInCartBeforeExpect, itemsInCart_before, f"Giỏ hàng ban đầu không khớp. Kỳ vọng: {itemsInCartBeforeExpect}, Thực tế: {itemsInCart_before}")
        except AssertionError as e: 
            self.verificationErrors.append(f"Lỗi xác minh Giỏ hàng ban đầu: {e}")
        except NoSuchElementException:
            self.verificationErrors.append("Lỗi: Không tìm thấy phần tử đếm giỏ hàng.")
            return

        try:
            numberItems_input = driver.find_element(By.XPATH, QUANTITY_INPUT_XPATH)
            addToCart_btn = driver.find_element(By.XPATH, ADD_TO_CART_BUTTON_XPATH)
            
            numberItems_input.click()
            numberItems_input.clear()
            numberItems_input.send_keys(numberItemsExpect)
            addToCart_btn.click()
            
        except NoSuchElementException:
            self.verificationErrors.append("Lỗi: Không tìm thấy trường số lượng hoặc nút Thêm vào giỏ hàng.")
            return
        try: 
            success_element = wait.until(EC.presence_of_element_located((By.XPATH, SUCCESS_MESSAGE_XPATH)))
            
            success_element.click() 
            
            self.assertEqual(textSuccessExpect," ".join(success_element.text.split()),
                             f"Thông báo thành công không khớp. Kỳ vọng: '{textSuccessExpect}', Thực tế: '{success_element.text}'")
        except AssertionError as e:
            self.verificationErrors.append(f"Lỗi xác minh Thông báo thành công: {e}")
        except TimeoutException:
            self.verificationErrors.append(f"Lỗi: Không tìm thấy thông báo thành công sau 10 giây. Kỳ vọng: '{textSuccessExpect}'")
        except StaleElementReferenceException:
             self.verificationErrors.append(f"Lỗi: Phần tử thông báo bị stale.")


        time.sleep(1) 
        try: 
            itemsInCart_after = driver.find_element(By.XPATH, CART_COUNT_XPATH).text
            self.assertEqual(itemsInCartAfterExpect, itemsInCart_after,
                             f"Giỏ hàng sau khi thêm không khớp. Kỳ vọng: {itemsInCartAfterExpect}, Thực tế: {itemsInCart_after}")
        except AssertionError as e: 
            self.verificationErrors.append(f"Lỗi xác minh Giỏ hàng sau khi thêm: {e}")
        except NoSuchElementException:
             self.verificationErrors.append("Lỗi: Không tìm thấy phần tử đếm giỏ hàng (sau khi thêm).")



def generate_test_cases():
    data_rows = load_csv_data()

    for index, row in enumerate(data_rows):

        def test(self, row=row): 
            self.run_test_case(
                row["itemsInCartBefore"],
                row["numberItems"],
                row["textSuccess"],
                row["itemsInCartAfter"],
                )

        test_name = f"test_add_to_cart_testcase_{row.get('testcase', index+1)}"
        setattr(BaseTest, test_name, test)


generate_test_cases()


if __name__ == "__main__":
    unittest.main()
