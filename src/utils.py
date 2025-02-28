# -*- coding: utf-8 -*-
"""
Created on Fri Feb 28 06:18:45 2025

@author: Wolfgang Reuter

"""

# =============================================================================
# Imports
# =============================================================================

import streamlit as st
OPENAI_API_KEY = st.secrets["openai"]["api_key"]

from langchain.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter

from PyPDF2 import PdfReader

# =============================================================================
# Functions
# =============================================================================

def load_stgb(FAISS_STORAGE_PATH, CHUNK_SIZE, OVERLAP):
    
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    
    vectorstore = FAISS.load_local(FAISS_STORAGE_PATH, embeddings, 
                                   allow_dangerous_deserialization=True)  
    
    return vectorstore
    
            

def load_pdf(pdf, CHUNK_SIZE, OVERLAP): 
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    if pdf is not None:
        pdf_reader = PdfReader(pdf)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
            
        # Split text into chunks
        text_splitter = CharacterTextSplitter(
            separator='\n', 
            chunk_size=CHUNK_SIZE, 
            chunk_overlap=OVERLAP,
            length_function=len)
        chunks = text_splitter.split_text(text)
    
    vectorstore = FAISS.from_texts(chunks, embeddings)
    
    return vectorstore
    


def get_relevant_legal_knowledge(query, vectorstore, N_RELEVANT_CHUNKS):
    retrieved_docs = vectorstore.similarity_search(query, k=N_RELEVANT_CHUNKS) 
    return " ".join([doc.page_content for doc in retrieved_docs])