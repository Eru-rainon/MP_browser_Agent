import os
import shutil
from bs4 import BeautifulSoup, Comment
from lxml import html
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate 
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ==========================================
# 1. DOM PROCESSING & EMBEDDING LOGIC
# ==========================================

class DomEmbedder:
    def __init__(self, embeddings_model):
        self.embeddings = embeddings_model
        self.vector_store_path = "./chromadb_showcase"
        self.clean_vector_store()
        self.vector_store = self._init_vectorstore()
        self.important_tags = [
            "form", "input", "button", "textarea", "select", "label", "a", "i", "svg", 
            "ul", "li", "nav", "table", "tr", "th", "td", "div", "span"
        ]

    def _init_vectorstore(self):
        return Chroma(
            collection_name="dom_collection",
            embedding_function=self.embeddings,
            persist_directory=self.vector_store_path
        )

    def clean_vector_store(self):
        if os.path.exists(self.vector_store_path):
            shutil.rmtree(self.vector_store_path)

    def clean_html(self, raw_html):
        """Removes scripts, styles, and hidden elements to reduce noise."""
        soup = BeautifulSoup(raw_html, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        for tag in soup.find_all(style=lambda value: value and 'display:none' in value):
            tag.decompose()
        for tag in soup.find_all(attrs={"hidden": True}):
            tag.decompose()
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()
        return str(soup)

    def describe_element(self, tag):
        """Creates a natural language description of a DOM element."""
        desc = [f"Element: {tag.tag}"]
        
        # attributes
        common_attrs = ["type", "placeholder", "aria-label", "name", "role", "id", "class", "href", "title", "value", "alt"]
        attributes = []
        for attr in common_attrs:
            val = tag.attrib.get(attr)
            if val:
                attributes.append(f"{attr}: {val}")
        
        if attributes:
            desc.append("Attributes: " + "| ".join(attributes))
            
        # Text content
        text = tag.text_content().strip()
        if text:
            trimmed = text[:100] + "..." if len(text) > 100 else text
            desc.append(f"text: {trimmed}")
            
        return " | ".join(desc)

    def process_and_embed(self, page):
        """Scrapes the page, processes the DOM, and embeds it."""
        print("Creating embeddings for the current page...")
        full_dom = page.content()
        cleaned_dom = self.clean_html(full_dom)
        tree = html.fromstring(cleaned_dom)
        
        documents = []
        for elem in tree.xpath("//*"):
            if elem.tag in self.important_tags:
                try:
                    xpath = elem.getroottree().getpath(elem)
                    description = self.describe_element(elem)
                    documents.append(Document(page_content=description, metadata={"xpath": xpath}))
                except Exception:
                    continue

        if documents:
            self.vector_store.add_documents(documents=documents)
            print(f"Successfully embedded {len(documents)} elements.")
        else:
            print("No suitable elements found to embed.")

    def search_similar_elements(self, query, k=5):
        return self.vector_store.similarity_search(query, k=k)


# ==========================================
# 2. LLM GENERATION LOGIC
# ==========================================

class XPathGenerator:
    def __init__(self, llm):
        self.llm = llm
        self.prompt = ChatPromptTemplate.from_template(
            """
             You are an expert web automation developer. 
             Based on the provided context, return **only** the XPATH of the web element that best matches the user's goal.
             
             Context (Candidate Elements): 
             {context}

             Goal: {question}

             Respond with ONLY the raw XPath string. Do not include markdown, explanations, or quotes.
            """
        )

    def find_xpath(self, embedder, user_prompt):
        # 1. Retrieve
        print(f"Searching for elements matching: '{user_prompt}'...")
        similar_docs = embedder.search_similar_elements(user_prompt)
        
        if not similar_docs:
            return "No matching elements found in embeddings."

        # 2. Format Context
        context_str = "\n\n".join(
            f"Description: {doc.page_content}\nXPath: {doc.metadata.get('xpath', 'N/A')}"
            for doc in similar_docs
        )

        # 3. Generate
        print("Asking LLM to select the best XPath...")
        messages = self.prompt.invoke({
            "question": user_prompt,
            "context": context_str
        })
        
        response = self.llm.invoke(messages)
        return response.content.strip()


# ==========================================
# 3. MAIN SHOWCASE LOOP
# ==========================================

def run_showcase():
    # Initialize Models
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

    embedder = DomEmbedder(embeddings)
    generator = XPathGenerator(llm)

    with sync_playwright() as p:
        # Browser Setup
        browser = p.chromium.launch(headless=False) 
        page = browser.new_page()

        # User Input: URL
        url = input("\n Enter the URL to analyze: ").strip()
        if not url.startswith("http"):
            url = "https://" + url
            
        print(f"Navigating to {url}...")
        try:
            page.goto(url, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)
        except Exception as e:
            print(f"Error loading page: {e}")
            return

        # Embed the Website
        embedder.process_and_embed(page)

        while True:
            user_prompt = input("\n Enter element to find (or 'exit'): ")
            if user_prompt.lower() in ["exit", "quit"]:
                break

            xpath = generator.find_xpath(embedder, user_prompt)
            
            # --- CRITICAL FIX: Add missing slash if LLM forgot it ---
            if not xpath.startswith("/") and not xpath.startswith("("):
                xpath = "/" + xpath
            # --------------------------------------------------------

            print(f" Trying XPath: {xpath}")

            try:
                # We use .first to just get the top match
                locator = page.locator(f"xpath={xpath}").first
                
                # Check if Playwright actually sees it
                if locator.count() > 0:
                    print(" Element found! Highlighting for 3 seconds...")
                    locator.scroll_into_view_if_needed() # Scroll to it first
                    locator.highlight()
                    page.wait_for_timeout(3000) # Pause so you can see it
                else:
                    print(" XPath was valid, but element not found on current page state.")
            except Exception as e:
                print(f" Playwright Error: {e}")

        browser.close()
        embedder.clean_vector_store()

if __name__ == "__main__":
    run_showcase()