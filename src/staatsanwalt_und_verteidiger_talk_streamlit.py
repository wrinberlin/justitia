# -*- coding: utf-8 -*-
"""
Created on Tue Dec  3 09:02:12 2024

@author: Wolfgang Reuter

USAGE: Run from command line: 
    streamlit run src\staatsanwalt_und_verteidiger_talk_streamlit.py
"""

# =============================================================================
# Imports
# =============================================================================

import streamlit as st
OPENAI_API_KEY = st.secrets["openai"]["api_key"]

import os
from pathlib import Path

from langchain_community.chat_models import ChatOpenAI
from langchain.prompts.chat import ChatPromptTemplate
from langchain.schema import SystemMessage, HumanMessage

# =============================================================================
# Paths and Variables
# =============================================================================

# Get the current working directory (will be the project root in Streamlit Cloud)
project_root = Path(os.getcwd()) 

IMAGE_PATH = project_root / "illustrations" / "justizia.jpg" 
N_RELEVANT_CHUNKS = 7
CHUNK_SIZE = 600
OVERLAP = 200

# Define the system messages
prosecutor_system_message = """
Sie sind ein Staatsanwalt, der einen einfachen Text analysiert.
Ihre Aufgabe ist wie folgt:
1. Lesen Sie den Eingabetext sorgfältig durch. Erfinden oder vermuten Sie keine Details, die nicht explizit erwähnt wurden.
2. Identifizieren Sie die beteiligte(n) Person(en) und die mutmaßliche(n) Straftat(en).
3. Plädieren Sie nur anhand der bereitgestellten Informationen für die härteste mögliche Strafe.
Sprechen Sie nicht von "meinem Mandanten", schließlich sind Sie Ankläger. 
Geben Sie NICHT direkt an, dass Sie für die härteste mögliche Strafe plädieren, schlagen Sie stattdessen ein konkretes Strafmaß vor.
Fügen Sie relevante Argumente hinzu, indem Sie relevante Gesetze und Paragraphen,
andere rechtliche Verweise und ähnliche Gerichtsurteile zitieren, sofern zutreffend.
Wenn Sie einen Text erhalten, der eine Würdigung der Verteidigung des ursprünglichen 
Textes darstellt, lassen Sie oben genannten Punkt 2. weg. Sie brauchen die Identifizierung der 
beteiligten Personen nicht zu wiederholen. Gehen Sie statt dessen auf die einzelnen 
Argumente dieser Würdigung ein - und widerlegen Sie sie, soweit möglich. 
"""

defence_system_message = """
Sie sind ein Anwalt (Verteidiger), der einen einfachen Text analysiert.
Ihre Aufgabe ist wie folgt:
1. Lesen Sie den Eingabetext sorgfältig durch. Erfinden oder vermuten Sie keine Details, die nicht explizit erwähnt wurden.
2. Argumentieren Sie nur anhand der bereitgestellten Informationen für die mildeste mögliche Strafe.
Geben Sie NICHT direkt an, dass Sie für die mildeste mögliche Strafe plädieren. Schlagen Sie stattdessen ein konkretes Strafmaß vor.
Fügen Sie relevante Argumente hinzu, indem Sie relevante Gesetze und Paragraphen,
andere rechtliche Verweise und ähnliche Gerichtsurteile zitieren, sofern zutreffend.
Wenn Sie einen Text erhalten, der eine Würdigung der Staatsanwaltschaft des ursprünglichen 
Textes darstellt, gehen Sie auf die einzelnen Argumente dieser Würdigung ein 
- und widerlegen Sie sie, soweit möglich. 
"""

# Define the prompts for both agents
prosecutor_prompt = ChatPromptTemplate.from_messages([ 
    SystemMessage(content=prosecutor_system_message),
    HumanMessage(content="Analysieren Sie den folgenden Text: {input_text} – und plädieren Sie für die härteste mögliche Strafe. Bennenen Sie das von Ihnen für richtig empfundene Strafmaß.")
])

defense_lawyer_prompt = ChatPromptTemplate.from_messages([ 
    SystemMessage(content=defence_system_message),
    HumanMessage(content="Analysieren Sie den folgenden Text: {input_text} – und plädieren Sie für die mildeste mögliche Strafe. Bennenen Sie das von Ihnen für richtig empfundene Strafmaß.")
])

# Initialize the Chat Models for each agent
prosecutor_agent = ChatOpenAI(model="gpt-4", temperature=0.2)  # Lowered temperature for precision
defense_lawyer_agent = ChatOpenAI(model="gpt-4", temperature=0.7)

def run_case_discussion(input_text):
    conversation_history = []

    # Step 1: Prosecutor's argument
    prosecutor_message = [
        SystemMessage(content=prosecutor_system_message.format(input_text=input_text)),
        HumanMessage(content=f"Analysieren Sie den folgenden Text: {input_text}. Plädieren Sie für die härteste mögliche Strafe.")
    ]
    prosecutor_response = prosecutor_agent.invoke(prosecutor_message)
    conversation_history.append(f"\n\n**Staatsanwalt:** {prosecutor_response.content}")

    # Step 2: Defense Lawyer's argument
    defense_message = [
        SystemMessage(content=defence_system_message.format(input_text=input_text)),
        HumanMessage(content=f"Analysieren Sie den folgenden Text: {input_text}. Plädieren Sie für die mildeste mögliche Strafe.")
    ]
    defense_response = defense_lawyer_agent.invoke(defense_message)
    conversation_history.append(f"\n\n**Verteidigung:** {defense_response.content}")

    # Step 3: Prosecutor responds to the defense's argument
    prosecutor_reply = [
        SystemMessage(content=prosecutor_system_message.format(input_text=input_text)),
        HumanMessage(content=f"Die Verteidigung argumentierte: '{defense_response.content}'. Widerlegen Sie dieses Argument und plädieren Sie für die härteste mögliche Strafe.")
    ]
    prosecutor_reply_response = prosecutor_agent.invoke(prosecutor_reply)
    conversation_history.append(f"\n\n**Staatsanwalt (widerspricht Verteidigung):** {prosecutor_reply_response.content}")
    
    # Step 4: Defense Lawyer responds to the prosecutor's reply
    defense_reply = [
        SystemMessage(content=defence_system_message.format(input_text=input_text)),
        HumanMessage(content=f"Der Staatsanwalt hat argumentiert: '{prosecutor_reply_response.content}'. Widerlegen Sie dieses Argument und plädieren Sie für die mildeste mögliche Strafe.")
    ]
    defense_reply_response = defense_lawyer_agent.invoke(defense_reply)
    conversation_history.append(f"\n\n**Verteidigung (widerspricht Staatsanwalt):** {defense_reply_response.content}")
    

    return conversation_history

st.set_page_config(page_title="Justitia")
# Streamlit App
st.title("Multi-Agent Legal Analysis")
st.write("Input a case description below to see the analysis from both the prosecutor and the defense lawyer.")

st.image(IMAGE_PATH)

# Input Text Area
input_text = st.text_area("Enter the case description here:", height=200)

if st.button("Analyze Case"):
    if input_text.strip():
        # Run the case discussion
        conversation_history = run_case_discussion(input_text)

        # Display results one after another
        for turn in conversation_history:
            st.write(turn)
    else:
        st.warning("Please enter a case description before clicking the analyze button.")
