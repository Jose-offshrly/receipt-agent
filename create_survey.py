from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import uuid
from langchain_core.messages import HumanMessage, BaseMessage
from langchain_community.chat_message_histories.file import FileChatMessageHistory
from config import config
from agents import survey_builder

memory = FileChatMessageHistory("data/survey_memory.json")

message_container = st.container(height=700, border=False)


def display_message(message: BaseMessage):
    with message_container:
        with st.chat_message(message.type):
            st.markdown(message.content, unsafe_allow_html=True)

            if message.additional_kwargs.get("metadata") and message.additional_kwargs["metadata"].get("response_type") == "survey":
                col1, col2 = st.columns([10, 2])
        
                with col1:
                    st.markdown('<p class="notification-text">Notify employees about this survey</p>', 
                            unsafe_allow_html=True)
                
                with col2:
                    if st.button("Notify", key=message.id):
                        print("clicked")
                        notify_message = HumanMessage(content="notify employees")
                        notify_message.additional_kwargs.setdefault("metadata", {})["hidden"] = True
                        assistant = survey_builder.invoke(
                            query=notify_message, 
                            memory=memory
                        )

                        display_message(assistant)


with message_container:
    for message in memory.messages:
        if not (message.additional_kwargs.get("metadata") and message.additional_kwargs["metadata"].get("hidden")):
            display_message(message)


####################################### Text Query

query = st.chat_input("Say something")
if query:

    message = HumanMessage(content=query, id=str(uuid.uuid4()))

    display_message(message)

    assistant = survey_builder.invoke(
        query=message, 
        memory=memory
    )

    display_message(assistant)