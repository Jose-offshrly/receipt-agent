import traceback
import random, string
from langchain_core.tools import tool 
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage, HumanMessage
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from models.xero import ReceiptLLM
from langchain_community.chat_message_histories.file import FileChatMessageHistory
from services.xero import accounting_create_receipt
from config import config
from services.xero import get_or_create_tax_rate

def random_alphanumeric(length=10):
    """Generate a random alphanumeric string."""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=length))


from pydantic import BaseModel, Field

class ReceiptSchema(BaseModel):
    receipt: ReceiptLLM = Field(description="Extracted receipt containing necesary fields to insert on xero")
    category: str = Field(description="User inputted category in this format [account code] - [account name], example 402 - Entertainment")

@tool(args_schema=ReceiptSchema)
def save_receipt_to_xero(receipt, category) -> str:
    """This tool accepts receipt and category then save to xero management app"""

    try:
        receipt = receipt.model_dump()
        tax_type = "NoTax"

        if receipt["TaxRate"] and receipt["TaxRate"] > 0 and receipt["TaxType"]:
            if receipt["TaxType"] != "NoTax":
                tax_type = f"{receipt['TaxType']} ({receipt['TaxRate']})%"
                get_or_create_tax_rate(tax_type, receipt["TaxRate"])


        line_items_with_tax = []
        print(tax_type)

        for item in receipt["LineItems"]:
            if item["IsTaxable"]:
                line_items_with_tax.append({
                    **item,
                    "TaxType": tax_type
                })
            else:
                line_items_with_tax.append(item)

        print(line_items_with_tax)

        receipts = {
            "Receipts": [
                {
                    "Date": receipt["Date"],
                    "LineItems": line_items_with_tax,
                    "Contact": receipt["Contact"],
                    "User": {
                        "UserID": config.user_id
                    },
                    "LineAmountTypes": receipt["LineAmountTypes"]
                }
            ]
        }

        accounting_create_receipt(receipts=receipts)
        return "Success saving the receipt"
    except BaseException as e:
        print(e)
        traceback.print_exc()
        return "Failed saving receipt"


tools = [save_receipt_to_xero]

model = ChatOpenAI(model="gpt-4o", temperature=0)

prompt = ChatPromptTemplate(
    [
        ("system", (
            "Your are helpful question and answer assistant"
            "Answer the following question based on this context\n\n"
            "Context: {context}"
            "Keep your answer concise"
            "You are equip with tools, make sure to route the query to appropriate tool if needed"
            "If given empty query, analyze the context and see if theres tool related to it and use it\n\n"

            "Instructions for Receipt Specific Query: "
            "1. If user submits an empty query, analyze the receipt and respond short summary of the receipt"
            "2. Format the output message in this ff format:"
                """
                    Here’s a summary of the important details from your [name of bill] receipt. This breakdown highlights the key charges and payment information.

                    [display here the very short summary of receipt, keep it 8 bullet points at most, list items purchased in bullet points, FInally compact the list]
                    
                    To help categorize this receipt properly, please choose a Category from the dropdown below.
                """
            "\n\n 3. Wait for the user to enter the category for the receipt, only save the receipt in xero when category/account is given by user"
            "4. 'Category' or 'Account' will be treated as the same" 
            "5. If account/category is given by user, automatically save the receipt to xero"
        )),
        
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ]
)

agent = create_openai_functions_agent(llm=model, tools=tools, prompt=prompt)
executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

def invoke(query: HumanMessage, memory: FileChatMessageHistory, active_context: str = "") -> AIMessage:

    response = executor.invoke({
        "input": query.content,
        "context": active_context,
        "chat_history": memory.messages
    })

    ai_message = AIMessage(response["output"], id=random_alphanumeric())

    if query.additional_kwargs.get("attachment"):
        ai_message.response_metadata = {
            "category": "NOT_SET"
        }

    memory.add_message(query)
    memory.add_message(ai_message)
    return ai_message
