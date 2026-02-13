from playwright.sync_api import sync_playwright, TimeoutError as PLTimeoutError
from PyPDF2 import PdfMerger
import io

class PlaywrightTools:
    def __init__(self,page):
        self.page = page
        self.snapshots = []

    def goToUrl(self,url):                                                                                                          #go to a specifid url
        self.page.goto(url,wait_until = "networkidle")                                                                                     
                                                                                                                                    
    def AccessElement(self, selector):                                                                                              #access an element using a selector
        return self.page.locator(f"xpath={selector.strip()}").first                                                                                    
                                                                                                                                    
    def validXpath(self, selector):                                                                                                 #check if the selector is valid
        try:                                                                                                                         
            element = self.AccessElement(selector)                                                                                   
            return element.is_visible() and element.is_enabled()                                                                    
        except Exception:                                                                                                            
            return False                                                                                                             
                                                                                                                                     
    def isScrollable(self, selector):                                                                                               #check if the element is scrollable
        elementToScroll = self.AccessElement(selector)                                                                               
        scrollHeight = self.page.evaluate("el => el.scrollHeight", elementToScroll)                                                  
        clientHeight = self.page.evaluate("el => el.clientHeight", elementToScroll)                                                  
        return scrollHeight > clientHeight                                                                                           
                                                                                                                                     
    def typeKeys(self, selector, keys):                                                                                             #type keys into an element
        element = self.AccessElement(selector)                                                                                       
        element.fill(keys)                                                                                                           
                                                                                                                                     
    def clickButton(self, selector):                                                                                                #click a button
        if self.validXpath(selector):                                                                                                
            elementToClick = self.AccessElement(selector)                                                                            
            elementToClick.click()                                                                                                   
            return "completed successfully"                                                                                          
        return"invalid XPATH"                                                                                                        
                                                                                                                                     
    def getText(self,selector):                                                                                                     #get text from an element
        elements = self.page.locator(selector)                                                                                       
        return " ".join([el.inner_text() for el in elements.all()])                                                                  
                                                                                                                                     
    def getScreenShot(self):                                                                                                         
        pdf_bytes = self.page.pdf(format="A4", print_background=True)
        self.snapshots.append(pdf_bytes)
        return f"Captured snapshot #{len(self.snapshots)}" 
    
    def merge_snapshots(self, output_path="final_output.pdf"):
        if not self.snapshots:
            return "No snapshots to merge."
        
        merger = PdfMerger()
        for i, pdf_data in enumerate(self.snapshots):
            merger.append(io.BytesIO(pdf_data))  # Use in-memory PDF
        merger.write(output_path)
        merger.close()
        return f"Merged PDF saved as {output_path}"
                                                                                                                                     
    def scrollBrowser(self, selector, pixels=500):                                                                                  #scroll an element using its selector
        if self.validXpath(selector):                                                                                                
            if self.isScrollable(selector):                                                                                          
                el = self.AccessElement(selector)                                                                                    
                self.page.evaluate("(el, y) => el.scrollTop += y", el, pixels)                                                       
                return "scrolled successfully"                                                                                       
            return "not a scrollable element"                                                                                        
        return "invalid XPATH"                                                                                                       
                                                                                                                                     
    def browserBack(self):                                                                                                          #go back in browser
        self.page.go_back(wait_until = "load")                                                                                       
        return                                                                                                                       
                                                                                                                                     
    def browserRefresh(self):                                                                                                       #reload a page
        self.page.reload(wait_until="load")                                                                                          
        return                                                                                                                       
                                                                                                                                     
    def pressEnterKey(self):                                                                                                        #press enter key          
        self.page.keyboard.press("Enter")                                                                                            
        return                                                                                                                       
                                                                                                                                     
    def getPageSource(self):                                                                                                        #get the DOM
        return self.page.content()                                                                                                   