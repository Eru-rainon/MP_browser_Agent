import os
import shutil
from NavigatorHead.finalAgent import WikiAgent
from langchain.chat_models import init_chat_model
from langchain_openai import OpenAIEmbeddings;
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()

folderToRemove = "chromadb_dom"
if os.path.exists(folderToRemove) and os.path.isdir(folderToRemove):
    shutil.rmtree(folderToRemove)

navigationLlm = init_chat_model(
    model="gpt-4o", model_provider="openai", temperature=0
)
EmbeddingsModel = OpenAIEmbeddings(
    deployment="text-embedding-3-large", model="text-embedding-3-large"
)

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False,
    )

    context = browser.new_context(
        no_viewport=True,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                     "(KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        extra_http_headers={
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.google.com"
        }
    )

    context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """)

    page = context.new_page()
    newAgent = WikiAgent(page=page, llm=navigationLlm, embeddingsModel=EmbeddingsModel)

    with open("prompt.txt", "r") as file:
        newprompt = file.read()

    

    newAgent.chat(newprompt)
    input("Agent finished execution. Press Enter to close the browser...")
    


