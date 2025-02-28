# -*- coding: utf-8 -*-
"""
Created on Tue Dec  3 09:02:12 2024

@author: Wolfgang Reuter

USAGE: Run from command line: 
    streamlit run src\staatsanwalt_und_verteidiger_talk_streamlit_1.py
"""

# =============================================================================
# Imports
# =============================================================================

import streamlit as st
OPENAI_API_KEY = st.secrets["openai"]["api_key"]

import os
from pathlib import Path

from langchain_community.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

import justitia_texts
import utils

# Get the current working directory (will be the project root in Streamlit Cloud)
project_root = Path(os.getcwd()) 

st.set_page_config(page_title="Justitia")

# =============================================================================
# Paths and Variables
# =============================================================================

IMAGE_PATH = project_root / "illustrations" / "justizia.jpg" 
N_RELEVANT_CHUNKS = 7
N_RELEVANT_CHUNKS_JUDGE = 10
CHUNK_SIZE = 600
OVERLAP = 200

FAISS_STORAGE_PATH = \
    project_root / "data" / f"faiss_stgb_{CHUNK_SIZE}_{OVERLAP}"

# =============================================================================
# Functions
# =============================================================================

def run_case_discussion(input_text):
    
    conversation_history = f"## Der Fall: ## \n{input_text}"

    # Step 1: Prosecutor's argument
    prosecutor_legal_knowledge = \
        utils.get_relevant_legal_knowledge(input_text, vectorstore, 
                                           N_RELEVANT_CHUNKS)
    prosecutor_message = [
        SystemMessage(content=f"{prosecutor_system_message}\n\nRelevante Strafrechtsinformationen: {prosecutor_legal_knowledge}"),
        HumanMessage(content=f"Analysieren Sie den folgenden Text: {input_text}. Plädieren Sie für die härteste mögliche Strafe.")
    ]
    prosecutor_response = prosecutor_agent.invoke(prosecutor_message)
    
    prosecutor_view = f"\n\n## Sicht des Staatsanwalts: ## \n{prosecutor_response.content}"
    st.write(prosecutor_view)
    conversation_history += prosecutor_view
    
    # Step 2: Defense Lawyer's argument
    defense_legal_knowledge = \
        utils.get_relevant_legal_knowledge(input_text, vectorstore, 
                                           N_RELEVANT_CHUNKS)
    defense_message = [
        SystemMessage(content=f"{defence_system_message}\n\nRelevante Strafrechtsinformationen: {defense_legal_knowledge}"),
        HumanMessage(content=f"Analysieren Sie den folgenden Text: {input_text}. Plädieren Sie für die mildeste mögliche Strafe.")
    ]
    
    defense_response = defense_lawyer_agent.invoke(defense_message)
    
    defense_view = f"\n\n## Sicht der Verteidigung: ## \n{defense_response.content}"
    st.write(defense_view)
    conversation_history += defense_view

    # Step 3: Prosecutor responds to the defense's argument
    prosecutor_reply_knowledge = \
        utils.get_relevant_legal_knowledge("Relevante Gegenargumente im Strafrecht", 
                                           vectorstore, N_RELEVANT_CHUNKS)
    prosecutor_reply = [
        SystemMessage(content=f"{prosecutor_system_message}\n\nRelevante Strafrechtsinformationen: {prosecutor_reply_knowledge}"),
        HumanMessage(content=f"Die Verteidigung argumentierte: '{defense_response.content}'. Widerlegen Sie dieses Argument und plädieren Sie für die härteste mögliche Strafe.")
    ]
    prosecutor_reply_response = prosecutor_agent.invoke(prosecutor_reply)
    prosecutor_objection = f"\n\n## Staatsanwalt widerspricht Verteidigung: ## \n{prosecutor_reply_response.content}"
    st.write(prosecutor_objection)
    conversation_history += prosecutor_objection
    
    # Step 4: Defense Lawyer responds to the prosecutor's reply
    defense_reply_knowledge = \
        utils.get_relevant_legal_knowledge("Gegenstrategien gegen die Argumente der Staatsanwaltschaft", 
                                           vectorstore, N_RELEVANT_CHUNKS)
    defense_reply = [
        SystemMessage(content=f"{defence_system_message}\n\nRelevante Strafrechtsinformationen: {defense_reply_knowledge}"),
        HumanMessage(content=f"Der Staatsanwalt hat argumentiert: '{prosecutor_reply_response.content}'. Widerlegen Sie dieses Argument und plädieren Sie für die mildeste mögliche Strafe.")
    ]
    defense_reply_response = defense_lawyer_agent.invoke(defense_reply)
    defense_objection = f"\n\n## Verteidigung widerspricht Staatsanwalt: ## \n{defense_reply_response.content}"
    st.write(defense_objection)
    conversation_history += defense_objection

    return conversation_history

def pass_judgement(conversation_history):
    # Step 1: Prosecutor's argument
    judge_legal_knowledge = \
        utils.get_relevant_legal_knowledge(conversation_history, vectorstore, 
                                           N_RELEVANT_CHUNKS_JUDGE)
    judge_message = [
        SystemMessage(content=f"{judge_system_message}\n\nRelevante Strafrechtsinformationen: {judge_legal_knowledge}"),
        HumanMessage(content=f"Fällen Sie ein gerechtes Urteil: {conversation_history}. Begründen Sie dieses Urteil.")
    ]
    judge_verdict = judge_agent.invoke(judge_message)
    
    judge_verdict = f"\n\n## Urteil: ## \n{judge_verdict.content}"
    st.write(judge_verdict)
    conversation_history += judge_verdict
    return conversation_history

# =============================================================================
# Load STGB vectorbase (or create it)
# =============================================================================

try: 
    vectorstore = utils.load_stgb(FAISS_STORAGE_PATH, CHUNK_SIZE, OVERLAP)
except: 
    pdf = st.file_uploader("Laden Sie das Strafgesetzbuch als PDF hoch", type="pdf", 
                           key="pdf_uploader_1")
    if pdf is not None:
        vectorstore = utils.load_pdf(pdf, CHUNK_SIZE, OVERLAP)

# =============================================================================
# Load system messages
# =============================================================================

# Define the system messages
prosecutor_system_message = justitia_texts.prosecutor_system_message
defence_system_message = justitia_texts.defence_system_message
judge_system_message = justitia_texts.judge_system_message

# =============================================================================
# Set up agents
# =============================================================================

# Initialize the Chat Models for each agent
prosecutor_agent = ChatOpenAI(model="gpt-4o", temperature=0.2, openai_api_key=OPENAI_API_KEY)  
defense_lawyer_agent = ChatOpenAI(model="gpt-4o", temperature=0.2, openai_api_key=OPENAI_API_KEY)
judge_agent = ChatOpenAI(model="gpt-4o", temperature=0.2, openai_api_key=OPENAI_API_KEY)


# Streamlit App
st.title("Multi-Agent Legal Analysis")
st.write("Input a case description below to see the analysis from both the prosecutor and the defense lawyer.")

st.image(IMAGE_PATH)

# Input Text Area
input_text = \
    st.text_area("Enter the case description here:", height=200, 
                 key="auto_textarea")
    
# Inject JavaScript to dynamically resize the text area
# Only works on streamlit community cloud
st.markdown("""
    <script>
        function autoResize() {
            var textarea = document.querySelector("textarea[data-testid='stTextArea']");
            textarea.style.height = "auto"; 
            textarea.style.height = (textarea.scrollHeight) + "px";
        }
        document.querySelector("textarea[data-testid='stTextArea']").addEventListener("input", autoResize);
        autoResize();  // Run on page load
    </script>
""", unsafe_allow_html=True)

if st.button("Analyze Case"):
    if input_text.strip():
        # Run the case discussion
        conversation_history = run_case_discussion(input_text)
        conversation_history_with_verdict = \
            pass_judgement(conversation_history)
            
    

    else:
        st.warning("Please enter a case description before clicking the analyze button.")
