from dotenv import load_dotenv
load_dotenv()

import requests, json
import streamlit as st
from PIL import Image
import uuid
from utils import get_image_base64, random_alphanumeric
from langchain_core.messages import HumanMessage, BaseMessage
from langchain_community.chat_message_histories.file import FileChatMessageHistory
from config import config
from utils import parse_receipt
from agents import receipt as receipt_agent
from services.xero import load_accounts

accounts = load_accounts()

active_context = ""


memory = FileChatMessageHistory("data/memory.json")
DEFAULT_CATEGORY = "Categorize to an account"


if "message_id" not in st.session_state:
    st.session_state.message_id = 1

if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None


message_container = st.container(height=700, border=False)


def handle_category_select(category):
    if not category or category == DEFAULT_CATEGORY:
        return
    
    message = HumanMessage(category, id=random_alphanumeric())

    # display_message(message) //add metadata
    message.response_metadata = {
        "hidden": True
    }

    # memory.add_message(message=message)

    assistant = receipt_agent.invoke(
        query=message, 
        memory=memory,
        active_context=active_context
    )

    display_message(assistant)



def display_message(message: BaseMessage):
    with message_container:
        with st.chat_message(message.type):
            if message.additional_kwargs.get("attachment"):
                st.image(message.additional_kwargs.get("attachment")["image_url"]["url"], width=300)
            else:
                st.markdown(message.content)
                if message.type == "ai" and message.response_metadata.get("category") == "NOT_SET":
                    form_key = f"form_{message.id}"  # Use message ID for unique form key
                    with st.form(key=form_key):
                        selected_category = st.selectbox(
                            'Select an option:',
                            [DEFAULT_CATEGORY, *sorted(accounts.keys(), key=lambda x: x.split(" - ", 1)[1])],
                            label_visibility="hidden"
                        )

                        action_col1, action_col2 = st.columns([8, 2], gap="medium")
                        with action_col1:
                            st.text("Please click the confirm button to finalize the receipt submission to Xero")
                        with action_col2:
                            submitted = st.form_submit_button("Confirm")
                            if submitted:
                                handle_category_select(selected_category)



with message_container:
    for message in memory.messages:
        if not message.response_metadata.get("hidden"):
            display_message(message)



# For displaying query input
col1, col2 = st.columns([1,12], gap="medium")


def handle_upload_change():
    if st.session_state.uploaded_img:
        st.session_state.uploaded_file = st.session_state.uploaded_img

        response = parse_receipt(st.session_state.uploaded_file)

        # Process response
        if response is None:
            st.error(f"Failed to process file: {response.status_code} - {response.text}")
        else:
            active_context = json.dumps(response["receipt"])

     
            img_type = st.session_state.uploaded_file.type
            raw_img = Image.open(st.session_state.uploaded_file)
            image_base64 = get_image_base64(raw_img)

            message = HumanMessage(
                content="", 
                id=random_alphanumeric(),
                additional_kwargs={
                    "attachment": {
                        "file_id": str(uuid.uuid4()),
                        "type": "receipt",
                        "image_url": {"url": f"data:{img_type};base64,{image_base64}"}
                    }
                }
            )

            display_message(message)

            assistant = receipt_agent.invoke(
                query=message, 
                memory=memory,
                active_context=active_context
            )

            display_message(assistant)
            st.session_state.uploaded_file = None

with col1:
    with st.popover(":paperclip:"):
        st.file_uploader(
            "Upload an image", 
            type=["png", "jpg", "jpeg"], 
            accept_multiple_files=False,
            key="uploaded_img",
            on_change=handle_upload_change
        )






####################################### Text Query

with col2:
    query = st.chat_input("Say something")

    if query:

        message = HumanMessage(content=query, id=random_alphanumeric(length=20))

        display_message(message)

        assistant = receipt_agent.invoke(
            query=message, 
            memory=memory,
            active_context=active_context
        )

        display_message(assistant)













# ECS

        # use cases
        # 1. Enter general topic
        # 2. Parse -> categorize -> save
        # 3. Automatically categorize if not specified
        # 4. parse and save automatically
        # 5. Follow up question (category id)

# attach image
# create tool for saving in file

        # if there is image upload stick to that context unless general question

# attach id to save context (mess)

# use cases
# 1. Enter general topic
# 2. Parse -> categorize -> save
# 3. Automatically categorize if not specified
# 4. parse and save automatically
# 5. Follow up question (category id)


# ask category details
# https://drive.google.com/uc?export=download&id=1Jy33av6Zcl_OeyU1SIhArrher7zdywJK






# PROBLEMS ENCOUNTERED
# OPENAI HAS H=SHORT TIMEOUT FOR DONWLOADING IMAGE









        # conversation id

        # create a file id (add description on what the image is for accurate retrieval)
        #     store structured and general descriptions of image
        #     The following steps may occur:
        #     Object detection: Recognizes items, text, or elements in the image (e.g., logos, icons).
        #     Text extraction: If text exists in the image, an OCR (Optical Character Recognition) system extracts it.
        #     Layout analysis: Determines how elements are visually organized (e.g., the text, images, and shapes on a business card).
        #     Semantic understanding: Models interpret content meaning, such as "this is a business card," and break it into logical sections.
        # then when a message has file id make it as reference as well (perform retrieval as well)
        # (if the message history has file id (agent will retrieve it))