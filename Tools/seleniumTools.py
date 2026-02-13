
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException,InvalidSelectorException
import base64
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys


class SeleniumTools:
    def __init__(self,driver):
        self.driver = driver


    def AccessElement(self,XPATH):
        return self.driver.find_element(By.XPATH,XPATH)

    def validXpath(self,XPATH):
        try:
            element = self.AccessElement(XPATH)
        except NoSuchElementException:
            return False
        except InvalidSelectorException:
            return False

        isDisplayed = element.is_displayed()
        isEnabled = element.is_enabled()

        if isDisplayed and isEnabled:
            return True
        else:
            return False

    def isScrollable(self,xpath):
        elementtoScroll = self.AccessElement(xpath)
        scroll_height = self.driver.execute_script("return arguments[0].scrollHeight", elementtoScroll)
        client_height = self.driver.execute_script("return arguments[0].clientHeight", elementtoScroll)

        return scroll_height > client_height

    def typeKeys(self,XPATH,keys):
   
        element = self.AccessElement(XPATH)
        element.send_keys(keys)
        return


    def clickButton(self,XPATH):
        if self.validXpath(XPATH):
            elementToClick = self.AccessElement(XPATH)
            elementToClick.click()
            return "completed succesfully"
        return "invalid XPATH"

    def getData(self,XPATH):
        element = self.AccessElement(XPATH)
        return element.text

    def goToUrl(self,url):
        self.driver.get(url)
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        return
        

    def getTextMultiple(self,XPATH):
        elements = self.driver.find_elements(By.XPATH,XPATH)
        result = ""
        for element in elements:
           result += element.text + " "
        return result.strip()
    
    def getScreenShot(self):
        screenShotPath = "web_shot.png"
        self.driver.save_screenshot(screenShotPath)
        with open(screenShotPath, "rb") as imag:
            b64_image = base64.b64encode(imag.read()).decode("utf-8")
        return b64_image

    def scrollbrowser(self,xpath):
        if self.validXpath(xpath):
            if self.isScrollable(xpath):
                elementToScroll = self.AccessElement(xpath)
                self.driver.execute_script("arguments[0].scrollTop += arguments[1];", elementToScroll, 500)
                return "scrolled Successfully"
            return "not a scrollable element"
        return "invalid Xpath"

    def browserBacK(self):
        self.driver.back()
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        return 

    def browserRefresh(self):
        self.driver.refresh()
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        return

    def pressEnterKey(self):
        ActionChains(self.driver).send_keys(Keys.ENTER).perform()
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        return

    def getpageSource(self):
        pageSource = self.driver.page_source
        return pageSource
        