

from langchain_chroma import Chroma

from langchain_core.documents import Document
from bs4 import BeautifulSoup,Comment
from lxml import html

from NavigatorHead.generator import Generator



class Embedder:
    def __init__(self,llm,embeddings):
        self.embeddings = embeddings
        self.domVectorStore = self._init_dom_vectorstore()
        self.currentUrl = None
        self.llm = llm
        self.generator = Generator(self,self.llm)
        self.graph = self.generator.buildGraph()
        self.needsReEmbedding = True
        self.currentDom = ""
        self.formattedText = []
        self.impotantTags = [
            # Form & Input Elements
            "form", "input", "button", "textarea", "select", "label", "fieldset", "legend", "option",

            # Links & Clickables
            "a", "area", "i","svg"

            # Lists & Menus
            "ul", "ol", "li", "menu", "menuitem", "nav",

            # Tables
            "table", "thead", "tbody", "tfoot", "tr", "th", "td", "caption",

            # Semantic Layout
            "section", "article", "header", "footer", "main", "aside",

            # General Containers
            "div", "span",

        ]

    def cleanHTML(self,html):
        soup = BeautifulSoup(html,"html.parser")
        for tag in soup(["script","style","noscript"]):
            tag.decompose()
        
        for tag in soup.find_all(style=lambda value: value and 'display:none' in value):
            tag.decompose()
       
        for tag in soup.find_all(attrs = {"hidden":True}):
            tag.decompose()
        
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()
        
        return str(soup)



    def describeElement(self,tag):
        desc = [f"Element: {tag.tag}"]

        Attributes = []
        common_attrs = ["type", "placeholder", "aria-label", "name", "role", "id", "class", "href", "title", "value", "alt"]
        for attribute in common_attrs:
            val = tag.attrib.get(attribute)
         
            if val:
                
                val = " ".join(val)
                Attributes.append(f"{attribute}: {val}")                          

        for attr_name, attr_val in tag.attrib.items():
            if attr_name.startswith("ng-") or attr_name.startswith("ng-reflect-"):
                Attributes.append(f"{attr_name}: {attr_val}")
        if Attributes:
            desc.append("Attributes: " + "| ".join(Attributes))
        text = tag.text_content().strip()
        if text:
            maxLength = 100
            trimmed = text[:maxLength]

            if len(text) > maxLength:
                trimmed += "..."

            desc.append(f"text: {trimmed}")
        return " | ".join(desc)


    def describeIcon(self, tag):
        desc = self.describeElement(tag)

        # Ensure base description has a trailing separator if needed
        if not desc.endswith(" | "):
            desc += " | "

        for attr in ["aria-label", "title", "alt"]:
            value = tag.get(attr)
            if value:
                desc += f"{attr}: {value} | "

        for attr in ["class", "id", "name"]:
            value = tag.get(attr)
            if value:
                desc += f"{attr}: {value} | "

        if tag.tag == "svg":
            title_el = tag.find(".//{*}title")
            desc_el = tag.find(".//{*}desc")
            if title_el is not None and title_el.text:
                desc += f"svg-title: {title_el.text.strip()} | "
            if desc_el is not None and desc_el.text:
                desc += f"svg-desc: {desc_el.text.strip()} | "

        text = tag.text_content().strip()
        if text:
            desc += f"text: {text} | "

        parent = tag.getparent()
        while parent is not None and parent.tag not in ["button", "a", "label", "div", "span"]:
            parent = parent.getparent()

        if parent is not None:
            parent_text = parent.text_content().strip()
            if parent_text and parent_text != text:
                desc += f"parent-text: {parent_text} | "

        return desc.strip(" | ")





    def preProcessDom(self,fullDom):
        
        fullDom = self.cleanHTML(fullDom)
        tree = html.fromstring(fullDom)
        documents = []

        for elem in tree.xpath("//*"):
            if elem.tag in self.impotantTags:
                xpath = elem.getroottree().getpath(elem)
                if elem.tag in ["svg", "i"]:
                    desc = self.describeIcon(elem)
                else:
                    desc = self.describeElement(elem)
                documents.append(Document(page_content=desc,metadata={"xpath":xpath}))
        return documents


    def _init_dom_vectorstore(self):
        return Chroma(
            collection_name="dom_collection",
            embedding_function=self.embeddings,  
            persist_directory="./chromadb_dom"          
        )

    def reset_dom_vectorstore(self):
        self.domVectorStore.delete_collection()
        self.domVectorStore = self._init_dom_vectorstore()

    def embeddDom(self,driver,):

        if not  self.needsReEmbedding:
            return
        try:
            
            self.reset_dom_vectorstore()
            self.currentUrl = driver.url
           
            fullDom = driver.content()
            if fullDom and fullDom == self.currentDom:
                self.needsReEmbedding = False
                return
            domDocs = self.preProcessDom(fullDom)
            
            domdocIDs = self.domVectorStore.add_documents(documents=domDocs)

            

            self.needsReEmbedding = False
            self.currentDom = fullDom
            return 
        except Exception as e:
            print(f"An error occurred while loading or processing the page: {e}")

        


        

    def simSearch(self,query,store):
        return store.similarity_search(query,k=8)

    def getXpath(self,goal,driver):
        self.embeddDom(driver)
        state = {
            "question": goal,
            "context": [],
            "answer": ""
        }
        result = self.graph.invoke(state)
        print(result["answer"])
        return result["answer"].strip()


    

    



    


