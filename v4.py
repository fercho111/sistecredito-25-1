# chatbot_service.py (Core Module)
import os
import re
import uuid
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.document_loaders import TextLoader

load_dotenv()

class ChatbotService:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.vectorstore = self._initialize_vectorstore()
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.3, max_tokens=200)
        self.retrieval_chain = self._create_chain()
        self.active_sessions: Dict[str, Dict[str, Any]] = {}  # Session ID: Financial Context

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

    def start_session(self, financial_context: Dict[str, Any]) -> str:
        """Initialize a new session with financial context. Returns session ID."""
        session_id = str(uuid.uuid4())
        self.active_sessions[session_id] = financial_context.copy()
        return session_id

    def process_message(
        self, 
        session_id: str, 
        user_input: str,
    ) -> Dict[str, Any]:
        """Process user input using stored financial context for the session."""
        # Retrieve session context
        if session_id not in self.active_sessions:
            raise ValueError("Invalid or expired session ID")
        
        financial_context = self.active_sessions[session_id]
        
        # Generate response
        response = self.retrieval_chain.invoke({
            "input": user_input,
            "amount_owed": financial_context["amount_owed"],
            "days_in_mora": financial_context["days_in_mora"]
        })
        
        # Auto-update debt if payment detected
        if payment := self._extract_payment(user_input):
            financial_context["amount_owed"] = max(0, financial_context["amount_owed"] - payment)
        
        return {
            "response": response["answer"],
            "session_id": session_id
        }

    def _extract_payment(self, text: str) -> float:
        matches = re.findall(r"\$\d+\.?\d*", text)
        return sum(float(match.replace("$", "")) for match in matches) if matches else 0
    
