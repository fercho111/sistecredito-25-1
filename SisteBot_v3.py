# chatbot_service.py (Core Module)
import os
import re
from typing import Dict, Any
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.document_loaders import TextLoader

load_dotenv()
docs_folder = "output_conversations"

class ChatbotService:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.vectorstore = self._initialize_vectorstore()
        self.llm = ChatOpenAI(model="gpt-4", temperature=0.3, max_tokens=150)
        self.retrieval_chain = self._create_chain()

    def _initialize_vectorstore(self):
        docs_folder = "output_conversations"
        documents = []
        for filename in os.listdir(docs_folder):
            if filename.endswith(".txt"):
                file_path = os.path.join(docs_folder, filename)
                loader = TextLoader(file_path, encoding="utf-8")
                documents.extend(loader.load())
        return Chroma.from_documents(documents, self.embeddings, collection_name="conversations")

    def _create_chain(self):
        retriever = self.vectorstore.as_retriever(search_kwargs={"k": 2})
        
        system_message = """Eres un asistente virtual especializado en negociación financiera para una institución de crédito. 
        Datos del cliente actual:
        - Deuda total: ${amount_owed:.2f}
        - Días en mora: {days_in_mora}

        Tu objetivo es ayudar a regularizar pagos considerando estos números específicos. Ofrece:
        1. Opciones basadas en el monto y días de mora
        2. Cálculos aproximados usando estos valores
        3. Referencia a políticas institucionales

        Contexto histórico (solo como ejemplos):
        {context}"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("human", "{input}"),
            ("system", "Recuerda: Actualiza tus respuestas según los datos más recientes. Deuda actual: ${amount_owed:.2f} | Días mora: {days_in_mora}")
        ])
        
        document_chain = create_stuff_documents_chain(self.llm, prompt)
        return create_retrieval_chain(retriever, document_chain)

    def process_message(
        self, 
        user_input: str, 
        financial_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        response = self.retrieval_chain.invoke({
            "input": user_input,
            "amount_owed": financial_context["amount_owed"],
            "days_in_mora": financial_context["days_in_mora"]
        })
        
        # Update context based on detected payments
        if payment := self._extract_payment(user_input):
            financial_context["amount_owed"] -= payment
        
        return {
            "response": response["answer"],
            "updated_context": financial_context
        }

    def _extract_payment(self, text: str) -> float:
        matches = re.findall(r"\$\d+\.?\d*", text)
        return sum(float(match.replace("$", "")) for match in matches) if matches else 0