
from typing_extensions import List,TypedDict
from langchain.prompts import ChatPromptTemplate
from langchain_core.documents import Document

from langgraph.graph import START,StateGraph

class State(TypedDict):
    question : str 
    answer: str
    context : List[Document]

class Generator:
    def __init__(self,embedder,llm):
        self.embedder = embedder
        self.llm = llm


        self.domPrompt = ChatPromptTemplate.from_template(
        """
             you are an expert web developer. based on the context return **only** the XPATH of the web element which can be used to achieve the goal.
             Selenium should be able to directly access that element using the XPATH provided as result.
             find the element that matches the most with the query and return only the xpath provided with it.
             Do NOT include any explanation, code formatting, markdown backticks, or comments.

             Respond with ONLY the raw XPath that was provided with the element description as plain text.

             Context : {context}
             Goal : {question}
             XPATH:  
        """
        )


    def retrieve(self, state: State):
        vec_store = self.embedder.domVectorStore 
        similiarDocs = self.embedder.simSearch(state["question"],vec_store)
        return {"context": similiarDocs}

    def generate(self,state:State):
        contextContents = "\n\n".join(
            f"Description: {doc.page_content}\nXPath: {doc.metadata.get('xpath', 'N/A')}"
            for doc in state["context"]
        )
        prompt = self.domPrompt 

        print(state["context"])

        messages = prompt.invoke({
            "question" : state["question"],
            "context"  : contextContents


            })
        response = self.llm.invoke(messages)
        return {"answer":response.content}

    def buildGraph(self):
        graphBuilder = StateGraph(State).add_sequence([self.retrieve,self.generate])
        graphBuilder.add_edge(START,"retrieve")
        return graphBuilder.compile()
