import csv
import unittest
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

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

class CombinedFilterProductLevel2Test(unittest.TestCase):
    
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

    def enter_price(self, xpath, price):
        driver = self.driver
        wait = WebDriverWait(driver, 10)
        
        print(f"Setting price {price} into {xpath}")
        try:
            # DYNAMIC XPATH USAGE
            input_element = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
            
            # --- FORCE VISIBILITY AND INTERACTIVITY ---
            driver.execute_script("""
                var el = arguments[0];
                el.style.display = 'block';
                el.style.visibility = 'visible';
                el.style.opacity = '1';
                el.style.zIndex = '99999';
                el.removeAttribute('hidden');
                if(el.parentElement) {
                    el.parentElement.style.display = 'block';
                    el.parentElement.style.visibility = 'visible';
                }
            """, input_element)
            
            driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", input_element)
            time.sleep(0.5)

            # Action Chains
            try:
                actions = ActionChains(driver)
                actions.move_to_element(input_element)
                actions.click()
                actions.pause(0.2)
                actions.key_down(Keys.CONTROL).send_keys("a").key_up(Keys.CONTROL)
                actions.send_keys(Keys.BACKSPACE)
                actions.send_keys(str(price))
                actions.send_keys(Keys.ENTER)
                actions.perform()
            except Exception as e:
                print(f"ActionChains failed: {e}. Fallback to JS.")
                driver.execute_script("arguments[0].value = arguments[1];", input_element, str(price))
                driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", input_element)
            
            time.sleep(1)
        except Exception as e:
            print(f"Element error with xpath {xpath}: {e}")

    def select_manufacturer(self, mfr_xpath):
        if not mfr_xpath: return # Skip if no xpath provided
        driver = self.driver
        wait = WebDriverWait(driver, 10)
        print(f"Selecting manufacturer via XPath: {mfr_xpath}")

        try:
            driver.execute_script("window.scrollBy(0, 300);")
            
            # Ensure panel open
            try:
                mfr_panel = driver.find_element(By.ID, "mz-filter-panel-0-1")
                if "show" not in mfr_panel.get_attribute("class"):
                    hdr = driver.find_element(By.XPATH, "//div[@data-target='#mz-filter-panel-0-1']")
                    driver.execute_script("arguments[0].click();", hdr)
            except: pass

            mfr_label = wait.until(EC.presence_of_element_located((By.XPATH, mfr_xpath)))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", mfr_label)
            time.sleep(0.5)
            
            try:
                mfr_label.click()
            except:
                driver.execute_script("arguments[0].click();", mfr_label)
            time.sleep(2)
        except Exception as e:
            print(f"Manufacturer selection failed: {e}")

    def run_flow_lv2(self, row_data):
        driver = self.driver
        
        # Unpack Data
        tc_id = row_data.get("TestCaseID")
        min_p = row_data.get("minPrice")
        max_p = row_data.get("maxPrice")
        flow = row_data.get("flow_type", "standard")
        
        # Unpack Config
        url = row_data.get("url")
        min_xpath = row_data.get("min_xpath")
        max_xpath = row_data.get("max_xpath")
        mfr_xpath = row_data.get("mfr_xpath")
        
        print(f"\n--- Running {tc_id} (Type: {flow}) ---")
        driver.set_window_size(1920, 1080)
        driver.get(url)
        time.sleep(2)

        try:
            price_panel = driver.find_element(By.ID, "mz-filter-panel-0-0")
            if "show" not in price_panel.get_attribute("class"):
                hdr = driver.find_element(By.XPATH, "//div[@data-target='#mz-filter-panel-0-0']")
                driver.execute_script("arguments[0].click();", hdr)
                time.sleep(1)
        except: pass

        # --- FLOW LOGIC ---
        if flow == 'mfr_first':
            # Select MFR first
            self.select_manufacturer(mfr_xpath)
            # Then Price
            self.enter_price(min_xpath, min_p)
            self.enter_price(max_xpath, max_p)
        else:
            # Price first (Standard)
            self.enter_price(min_xpath, min_p)
            self.enter_price(max_xpath, max_p)
            # Then MFR
            self.select_manufacturer(mfr_xpath)

        # Verification Logic (Optional Visual Check)
        time.sleep(2)
        # Check for products
        rows = driver.find_elements(By.XPATH, "//div[contains(@class, 'product-thumb')]")
        if len(rows) > 0:
            print(f"[{tc_id}] Products found: {len(rows)}")
        else:
            try:
                msg = driver.find_element(By.XPATH, "//*[contains(text(), 'There are no products')]")
                print(f"[{tc_id}] 'No products' message detected.")
            except:
                print(f"[{tc_id}] No products found (and no msg detected).")

def generate_test_cases():
    data_rows = load_csv_data("../data/filter_product_lv2.csv") 

    for index, row in enumerate(data_rows):
        def test(self, row=row): 
            self.run_flow_lv2(row)
        
        tc_id = row.get("TestCaseID", f"Row_{index}")
        safe_name = f"test_lv2_{tc_id}"
        setattr(CombinedFilterProductLevel2Test, safe_name, test)

generate_test_cases()

if __name__ == "__main__":
    unittest.main()
