# -*- coding: utf-8 -*-
"""
Created on Fri Feb 28 05:49:30 2025

@author: Wolfgang Reuter

Stores the STGB chunks in a FAISS database. 

TODO: Add information about from where to run this script (due to relative
      paths)
TODO: Make more generic for other data (like sentences, etc.)
"""

# =============================================================================
# Imports
# =============================================================================

import os

from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

from pathlib import Path

# Get the current working directory (will be the project root in Streamlit Cloud)
project_root = Path(os.getcwd())
assert False
# =============================================================================
# Paths and Variables
# =============================================================================

SAVE_DATA = True

CHUNK_SIZE = 600
OVERLAP = 200

STGB_PATH = r"C:\Agents\data\StGB.pdf"

FAISS_STORAGE_PATH = \
    project_root / "data" / f"faiss_stgb_{CHUNK_SIZE}_{OVERLAP}"
assert False
# =============================================================================
# Set up data folder
# =============================================================================

if not os.path.exists(FAISS_STORAGE_PATH): 
    os.makedirs(FAISS_STORAGE_PATH, exist_ok=True)

# =============================================================================
# Generate and store FAISS data
# =============================================================================

pdf_loader = PyPDFLoader(STGB_PATH)
pages = pdf_loader.load()

text_splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, 
                                               chunk_overlap=OVERLAP)
chunks = text_splitter.split_documents(pages)

vectorstore = FAISS.from_documents(chunks, OpenAIEmbeddings())

if SAVE_DATA: 
    # Save FAISS index locally
    vectorstore.save_local(FAISS_STORAGE_PATH)

