
'''
from dotenv import load_dotenv
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.openrouter import OpenRouter
import os
import logging
import sys
from pathlib import Path
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
    Settings
)

# Load the environment variables
load_dotenv(override=True)

# Set up the LLM
llm = OpenRouter(
    api_key=os.getenv('OPENAI_API_KEY'),
    model="google/gemma-2-9b-it:free",
    max_tokens=256
)
Settings.llm = llm

Settings.embed_model = HuggingFaceEmbedding(
    model_name="all-MiniLM-L6-v2"
)

# Create a logger instance for debugging 
logger = logging.getLogger(__name__)
stdoutHandler = logging.StreamHandler(stream=sys.stdout)
fileHandler = logging.FileHandler("logs.txt", mode="w")
logger.addHandler(stdoutHandler)
logger.addHandler(fileHandler)

def get_index_from_documents(docs_dir: str, persist_dir: str) -> VectorStoreIndex:
    """Maintains index with full change detection including deletions"""
    Path(persist_dir).mkdir(parents=True, exist_ok=True)
    
    # Load documents with filename-based IDs
    documents = SimpleDirectoryReader(
        docs_dir,
        filename_as_id=True,
        file_metadata=lambda x: {"source": x}
    ).load_data()
    
    try:
        # Load existing index
        storage_context = StorageContext.from_defaults(persist_dir=persist_dir)
        index = load_index_from_storage(storage_context)
        logger.info("Existing index has been loaded !")

        # Get document IDs from both sources
        current_ids = {doc.metadata["source"] for doc in documents}
        stored_ids = {info.metadata["source"] for info in index.ref_doc_info.values()}

        # Handle updates/new docs
        refreshed_docs = index.refresh_ref_docs(
            documents,
            update_kwargs={"delete_kwargs": {"delete_from_docstore": True}}
        )
        changes = sum(refreshed_docs)

        # Detect deletions (stored sources that aren't in current docs)
        deleted_ids = stored_ids - current_ids
        if deleted_ids:
            print(f"Removing {len(deleted_ids)} deleted documents ... ")
            # Iterate over a copy of keys to avoid mutation during iteration
            for doc_id in list(index.ref_doc_info.keys()):
                ref_doc_info = index.ref_doc_info[doc_id]
                source = ref_doc_info.metadata.get("source")
                if source in deleted_ids:
                    index.delete_ref_doc(doc_id, delete_from_docstore=True)
        
        # Persist only if changes occurred
        if changes or deleted_ids:
            index.storage_context.persist(persist_dir=persist_dir)
            logger.info(f"Index updated: {changes} docs updated, {len(deleted_ids)} removed")
        else: 
            logger.info("No changes in the cadence docs and index loaded from disk")

    except Exception as e:
        # Create new index if none exists
        logger.info("Creating new index ....")
        index = VectorStoreIndex.from_documents(documents)
        index.storage_context.persist(persist_dir=persist_dir)
        logger.info("Documents indexed successfully !")
    
    return index

# create or update the index
index = get_index_from_documents(
    docs_dir="Tunisia_Data",
    persist_dir="storage/cache"
)

'''