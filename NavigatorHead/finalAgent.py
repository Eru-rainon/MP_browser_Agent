
from langchain.agents import initialize_agent,AgentType
from langchain.callbacks import get_openai_callback
from langchain_core.tools import Tool
from NavigatorHead.embedder import Embedder
from Tools.playwrightTools import PlaywrightTools









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


         








    