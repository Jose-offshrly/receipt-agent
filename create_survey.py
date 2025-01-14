from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import uuid
from langchain_core.messages import HumanMessage, BaseMessage
from langchain_community.chat_message_histories.file import FileChatMessageHistory
from config import config
from agents import survey_builder
from streamlit_authenticator import Authenticate


authenticator = Authenticate(
    names=st.secrets["credentials"]["names"],
    usernames=st.secrets["credentials"]["usernames"],
    passwords=st.secrets["credentials"]["passwords"],
    cookie_name=st.secrets["cookie"]["name"],
    key=st.secrets["cookie"]["key"],
    cookie_expiry_days=st.secrets["cookie"]["expiry_days"]
)


name, authentication_status, username = authenticator.login('Login', 'main')

def render():
    memory = FileChatMessageHistory(f"data/{username}_survey_memory.json")

    if authentication_status:
        with st.sidebar:
            st.text("Make sure to clear chat, to save tokens")

            def clear():
                if memory:
                    memory.clear()
            st.button("Clear Chat", on_click=clear)
    
            st.divider()

    authenticator.logout('Logout', 'sidebar')

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

    

def main():
    if authentication_status:
        render()

    elif authentication_status == False:
        st.error('Username/password is incorrect')
    elif authentication_status == None:
        st.warning('Please enter your username and password')


if __name__ == "__main__":
    main()