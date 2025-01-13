from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import uuid
from langchain_core.messages import HumanMessage, BaseMessage
from langchain_community.chat_message_histories.file import FileChatMessageHistory
from config import config
from agents import survey_taker
from survey_options import survey_options

memory = FileChatMessageHistory("data/survey_taker.json")

message_container = st.container(height=700, border=False)

VERY_SATISFIED="Very Satisfied"
SATISFIED="Satisfied"
NEUTRAL="Neutral"
DISSATISFIED="Dissatisfied"
VERY_DISSATISFIED="Very Dissatisfied"

SUFFIX_ID_FOR_CTA = "--SELECT_ANSWER--"

def handle_button_clicked(id, answer):
    answer_message = HumanMessage(content=answer, id=str(uuid.uuid4()))
    answer_message.additional_kwargs.setdefault("metadata", {})
    answer_message.additional_kwargs["metadata"]["hidden"] = True

    assistant = survey_taker.invoke(
        query=answer_message, 
        memory=memory
    )


    display_message(assistant)


def display_message(message: BaseMessage):
    if message.additional_kwargs["metadata"].get("hidden"):
        return
    with message_container:
        with st.chat_message(message.type):
            
            if message.content.strip().endswith(SUFFIX_ID_FOR_CTA):
                message.content = message.content.strip()[:-len(SUFFIX_ID_FOR_CTA)]

            st.markdown(message.content, unsafe_allow_html=True)

            if message.additional_kwargs.get("metadata") and message.additional_kwargs["metadata"].get("response_type") == "survey_question":
                value = survey_options(key=f"sq-{message.id}")
                if value:
                    handle_button_clicked(message.id, value)
                    


with message_container:
    for message in memory.messages:
        if not (message.additional_kwargs.get("metadata") and message.additional_kwargs["metadata"].get("hidden")):
            display_message(message)


####################################### Text Query

query = st.chat_input("Say something")
if query:
    print("Running query from query")
    message = HumanMessage(content=query, id=str(uuid.uuid4()))
    message.additional_kwargs.setdefault("metadata", {})
    if query == "--START--":
        message.additional_kwargs["metadata"] = {"hidden": True}

    display_message(message)

    assistant = survey_taker.invoke(
        query=message, 
        memory=memory
    )


    display_message(assistant)