from playwright.sync_api import sync_playwright, TimeoutError as PLTimeoutError

class PlaywrightTools:
    def __init__(self,page):
        self.page = page
        self.snapshots = []

    def goToUrl(self,url):                                                                                                          
        self.page.goto(url,wait_until = "networkidle")                                                                                     
                                                                                                                                    
    def AccessElement(self, selector):                                                                                             
        return self.page.locator(f"xpath={selector.strip()}").first                                                                                    
                                                                                                                                    
    def validXpath(self, selector):                                                                                               
        try:                                                                                                                         
            element = self.AccessElement(selector)                                                                                   
            return element.is_visible() and element.is_enabled()                                                                    
        except Exception:                                                                                                            
            return False                                                                                                             
                                                                                                                                                                                            
                                                                                                                                     
    def typeKeys(self, selector, keys):                                                                                           
        element = self.AccessElement(selector)                                                                                       
        element.fill(keys)                                                                                                           
                                                                                                                                     
    def clickButton(self, selector):                                                                                               
        if self.validXpath(selector):                                                                                                
            elementToClick = self.AccessElement(selector)                                                                            
            elementToClick.click()                                                                                                   
            return "completed successfully"                                                                                          
        return"invalid XPATH"                                                                                                                                                                                                           
                                                                                                                                     
    def browserBack(self):                                                                                                          
        self.page.go_back(wait_until = "load")                                                                                       
        return                                                                                                                       
                                                                                                                                     
    def browserRefresh(self):                                                                                                       
        self.page.reload(wait_until="load")                                                                                          
        return                                                                                                                       
                                                                                                                                     
    def pressEnterKey(self):                                                                                                          
        self.page.keyboard.press("Enter")                                                                                            
        return                                                                                                                       
                                                                                                                                     
    def getPageSource(self):                                                                                                        
        return self.page.content()                                                                                                   