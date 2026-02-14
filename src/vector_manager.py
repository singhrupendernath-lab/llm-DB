import os
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from src.config import Config

class VectorManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.persist_directory = "./chroma_db"

        # Use a lightweight open-source embedding model
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

        # Collection for database schema
        self.schema_db = Chroma(
            collection_name="db_schema",
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory
        )

        # Collection for chat history (Self-learning)
        self.chat_db = Chroma(
            collection_name="chat_history",
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory
        )

        # Initialize schema if empty
        if len(self.schema_db.get()['ids']) == 0:
            self.refresh_schema()

    def refresh_schema(self):
        """Extracts schema from DB and populates Chroma."""
        print("Refreshing schema in Vector DB...")
        db = self.db_manager.get_db()

        # Get table names
        try:
            table_names = db.get_usable_table_names()
        except Exception:
            # Fallback for some SQLDatabase versions
            table_names = db._inspect_table_names()

        documents = []
        for table_name in table_names:
            # Get schema for each table
            try:
                table_info = db.get_table_info([table_name])
                doc = Document(
                    page_content=table_info,
                    metadata={"table_name": table_name, "type": "schema"}
                )
                documents.append(doc)
            except Exception as e:
                print(f"Error extracting schema for {table_name}: {e}")

        if documents:
            self.schema_db.add_documents(documents)
            print(f"Added {len(documents)} tables to Vector DB.")

    def search_relevant_schema(self, query, k=3):
        """Returns relevant table schemas for a given query."""
        results = self.schema_db.similarity_search(query, k=k)
        return "\n\n".join([r.page_content for r in results])

    def get_relevant_tables(self, query, k=3):
        """Returns names of relevant tables."""
        results = self.schema_db.similarity_search(query, k=k)
        return [r.metadata["table_name"] for r in results]

    def add_chat_interaction(self, question, answer, sql_queries=None, session_id="default"):
        """Stores a chat interaction for future retrieval (self-learning)."""
        content = f"Question: {question}\nAnswer: {answer}"
        if sql_queries:
            content += f"\nSQL Queries Used: {', '.join(sql_queries)}"

        doc = Document(
            page_content=content,
            metadata={"session_id": session_id, "type": "chat_interaction"}
        )
        self.chat_db.add_documents([doc])
        print(f"Saved interaction to Chat Vector DB (session: {session_id}).")

    def search_relevant_chat(self, query, k=2):
        """Retrieves relevant past interactions to provide context."""
        results = self.chat_db.similarity_search(query, k=k)
        if not results:
            return ""

        context = "Learned Knowledge from past interactions:\n"
        for r in results:
            context += f"---\n{r.page_content}\n"
        return context
