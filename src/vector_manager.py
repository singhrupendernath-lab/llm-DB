import os
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from config import Config

class VectorManager:
    def __init__(self, db_manager, collection_name="db_schema"):
        self.db_manager = db_manager
        self.persist_directory = "./chroma_db"

        # Use a lightweight open-source embedding model
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

        self.vector_db = Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory
        )

        # Initialize schema if empty
        if len(self.vector_db.get()['ids']) == 0:
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
            self.vector_db.add_documents(documents)
            print(f"Added {len(documents)} tables to Vector DB.")

    def search_relevant_schema(self, query, k=3):
        """Returns relevant table schemas for a given query."""
        results = self.vector_db.similarity_search(query, k=k)
        return "\n\n".join([r.page_content for r in results])

    def get_relevant_tables(self, query, k=3):
        """Returns names of relevant tables."""
        results = self.vector_db.similarity_search(query, k=k)
        return [r.metadata["table_name"] for r in results]
