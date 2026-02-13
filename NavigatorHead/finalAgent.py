
from langchain.agents import initialize_agent,AgentType
from langchain.callbacks import get_openai_callback
import json
from langchain_core.tools import Tool
from NavigatorHead.embedder import Embedder
from Tools.playwrightTools import PlaywrightTools
from Tools.jsonTools import JsonTools
from NavigatorHead.textExtractor import textExtractor









class WikiAgent:
    def __init__(self,page,llm,embeddingsModel):
        self.llm = llm
        self.embedder = Embedder(self.llm,embeddingsModel)
        self.textExtractor = textExtractor(self.embedder)
        self.agentExecutor = None
        self.page = page
        self.playwrightTools = PlaywrightTools(self.page)
        self.jsonTools = JsonTools()
        self.tools = self.buildTools()
        self.initialUrl = None 

        
 
        self.buildAgent()
            
    def buildTools(self):
        return [
                
             
                Tool(
                        name = "get_XPATH",
                        func=lambda goal: self.getXPath(goal),
                        description=(
                            "Use this tool to interact with a webpage and find the XPath of an element most suited for the current step. "
                            "goal should be of the format 'find the XPATH of the 'required element' "
                            "do **not** use this tool to extract text data or find information about a webpage"
                        )
                    ),
                Tool(
                        name="go_to_url",
                        func=lambda url: self.goToUrl(url),
                        description="Use this tool to open a webpage by URL. Input should be a valid URL string **without any quotation marks** "
                    ),
                Tool(
                        name="click_button",
                        func=lambda xpath: self.clickButton(xpath),
                        description="Use this tool to click a button or element on the page. Input must be a valid XPath string."
                    ),
                Tool(
                        name="type_keys",
                        func=lambda x: self._parse_and_type(x),
                        description="Use this tool to type text into a web element. "
                                    "Input should be in the format: XPATH ||| TEXT_TO_TYPE"
                    ),
                Tool(
                        name="browser_back_button",
                        func=lambda _:self.browserBack(),
                        description="use this tool to navigate to the previous page"

                    ),
                Tool(
                        name="reload_current_page",
                        func=lambda _:self.browserRefresh(),
                        description="use this tool reload the current page"

                    ),
                Tool(
                        name="press_enter_key",
                        func=lambda _:self.pressEnterKey(),
                        description="use this tool to press the enter key"
                    ),
                Tool(
                        name="get_text_from_website",
                        func=lambda _:self.getTextFromWebsite(),
                        description="use this tool to extract text data from the current webpage. no input required"
                    ),
                Tool(
                    name = "load_from_json",
                    func=lambda filename: self.loadDataFromJson(filename),
                    description="use this tool to load data from a json file. input should be the filename as a string"
                    
                ),

                Tool(
                    name = "load_previous_flow",
                    func = lambda url : self.loadContext(url),
                    description=(
                        "Checks for saved workflows associated with the given URL. "
                        "If found and relevant, use the steps to complete the current task. Input must be the current website's URL."
                    )
                    
                ),
                Tool(
                    name = "load_previous_xpaths",
                    func = lambda url : self.loadXpaths(url),
                    description="use this tool to check if there are any existing Xpaths for the current url. if Xpaths are obtained, try completing the goal using those Xpaths first. Input must be the current website's URL"
                ),
                Tool(
                    name = "save_flow_to_json",
                    func = lambda steps:self.saveFlowtoJson(steps),
                    description="use this to save the current workflow to a json for future reference. input should be a string containing steps that was followed in the current session."
                ),
                Tool(
                    name="save_Xpaths_to_json",
                    func=lambda xpaths:self.saveXPathstoJson(xpaths),
                    description="use this after a task to save the xpaths that were used in this flow. input should a string in the format 'element':'xpath'"
                ),
                Tool(
                    name="take_screenshot",
                    func=lambda _:self.playwrightTools.getScreenShot(),
                    description="use this tool to take a screenshot. No input required"
                ),
                Tool(
                    name="save_screenshots",
                    func=lambda _:self.playwrightTools.merge_snapshots(),
                    description="use this tool to save all screenshots. No input required"
                )

             
                
            ]


    #====================================TOOLS USED BY AGENT=========================================================
    def getXPath(self,goal):
        return self.embedder.getXpath(goal,self.page)

    def goToUrl(self,url):
        if not self.initialUrl:
            self.initialUrl = url
            self.currentflow = []
        self.playwrightTools.goToUrl(url)
        return f"navigated to {url} successfully"

    
        

    def _parse_and_type(self, x):
        try:
            xpath, keys = x.split("|||")
            if self.playwrightTools.validXpath(xpath.strip()):
                self.playwrightTools.typeKeys(xpath.strip(),keys.strip())
                return "completed successfully"
            return "invalid xpath"
        except ValueError:
            return "Invalid format. Please use: XPATH ||| TEXT_TO_TYPE"


    def clickButton(self,Xpath):
        self.embedder.needsReEmbedding = True
        return self.playwrightTools.clickButton(Xpath)

    def downloadFile(self,Xpath):
        self.embedder.needsReEmbedding = True
        return self.playwrightTools.clickAndDownload(Xpath)
        

    def scrollWebpage(self,xpath):
        return self.playwrightTools.scrollBrowser(xpath)
        

    def browserBack(self):
        self.playwrightTools.browserBack()
        self.embedder.needsReEmbedding = True
        return "navigated one page back successfully"

    def browserRefresh(self):
        self.playwrightTools.browserRefresh()
        self.embedder.needsReEmbedding = True
        return "page refreshed successfully"

    def pressEnterKey(self):
        self.playwrightTools.pressEnterKey()
        self.embedder.needsReEmbedding = True
        return "Entered successfully"

    def getTextFromWebsite(self):
        html = self.playwrightTools.getPageSource()
        text = self.textExtractor.getTextData(html)
        if text:
            return "text data extracted from webpage successfully"
        return "unable to extract text data from webpage, try again after reloading the page"


        #flow logging


    def loadContext(self,url):
        workflow = "no workflow currently loaded"
        with open("flow.json","r") as flow:
            data = json.load(flow)
            for entry in data:
                if entry["url"] == url:
                    workflow = entry["steps"]
                    break
        return workflow

    def loadXpaths(self,url):
        workflow = "no XPATHS currently loaded"
        with open("Xpaths.json","r") as flow:
            data = json.load(flow)
            for entry in data:
                if entry["url"] == url:
                    workflow = entry["Xpaths"]
                    break
        return workflow

    def loadDataFromJson(self,filepath):
        return self.jsonTools.loadCredentials(filepath)

    def storeDatatoJson(self,data):
        return self.jsonTools.storetoJson(data)

    def saveFlowtoJson(self,steps):
        flowData = []

        try:
            with open("flow.json", 'r') as flow:
                flowData = json.load(flow)
        except FileNotFoundError:
            flowData = []

  
        flowData = [entry for entry in flowData if entry["url"] != self.initialUrl]


        flowData.append({
            "url": self.initialUrl,
            "steps":steps
        })

        with open("flow.json", 'w') as flow:
            json.dump(flowData, flow, indent=2)

        return f"Flow saved successfully for URL: {self.initialUrl}"


    def saveXPathstoJson(self,Xpaths):
        flowData = []

        try:
            with open("Xpaths.json", 'r') as flow:
                flowData = json.load(flow)
        except FileNotFoundError:
            flowData = []

  
        flowData = [entry for entry in flowData if entry["url"] != self.initialUrl]


        flowData.append({
            "url": self.initialUrl,
            "Xpaths":Xpaths
        })

        with open("Xpaths.json", 'w') as flow:
            json.dump(flowData, flow, indent=2)

        return f"Xpaths saved successfully for URL: {self.initialUrl}"




      #====================================TOOLS USED BY AGENT=========================================================






    def buildAgent(self):
        self.agentExecutor = initialize_agent(
                tools=self.tools,
                llm=self.llm,
                agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                verbose = True,
                max_execution_time=1200,
                 max_iterations=600,
                 handle_parsing_errors=True
            )
    

    def chat(self, prompt):
        from langchain.callbacks import get_openai_callback
       
        if prompt == "":
            newprompt = input("enter the prompt")
        else:
            newprompt = prompt

        with get_openai_callback() as cb:
            response = self.agentExecutor.invoke({"input": newprompt})
            print(f"agent: {response}\n")
            print(f"Token usage - Prompt: {cb.prompt_tokens}, Completion: {cb.completion_tokens}, Total: {cb.total_tokens}, Cost: ${cb.total_cost:.4f}")


         








    