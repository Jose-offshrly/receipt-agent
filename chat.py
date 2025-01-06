import traceback
import random, string
from langchain_core.tools import tool 
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage, BaseMessage
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from models.xero import ReceiptLLM, AccountLLM
from data import load_accounts
from langchain_community.chat_message_histories.file import FileChatMessageHistory
from services.xero import accounting_create_receipt
from langchain_core.output_parsers import JsonOutputParser
from config import config

from services.xero import get_or_create_tax_rate

def random_alphanumeric(length=10):
    """Generate a random alphanumeric string."""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=length))


@tool
def save_receipt_to_xero(receipt: ReceiptLLM) -> str:
    """This tool accepts receipt data and save to xero"""

    try:
        receipt = receipt.model_dump()
        tax_type = "NoTax"

        if receipt["TaxRate"] and receipt["TaxRate"] > 0:
            tax_type = f"VAT ({receipt['TaxRate']})%"
            get_or_create_tax_rate(tax_type, receipt["TaxRate"])

        receipts = {
            "Receipts": [
                {
                    "Date": receipt["Date"],
                    "LineItems": receipt["LineItems"],
                    "Contact": receipt["Contact"],
                    "User": {
                        "UserID": config.user_id
                    },
                    "LineAmountTypes": receipt["LineAmountTypes"],
                    # "SubTotal": receipt.subtotal,
                    # "TotalTax": receipt.total_tax,
                    # "Total": receipt.subtotal,

                }
            ]
        }

        accounting_create_receipt(receipts=receipts)
        return "Success saving the receipt"
    except BaseException as e:
        print(e)
        traceback.print_exc()
        return "Failed saving receipt"


@tool
def get_account_details(account: str) -> AccountLLM:
    """This tool accepts account name [code - name] provided by user and will return details about that account such as account_id, account_code etc"""
    print(account)
    accounts = load_accounts()
    account = accounts[account]
  
    return AccountLLM(
        account_id = account["AccountID"],
        account_code = account["Code"],
        account_name = account["Name"],
        status = account["Status"],
        type = account["Type"],
        tax_type = account["TaxType"],
        description = account["Description"]
    )

tools = [get_account_details, save_receipt_to_xero]

model = ChatOpenAI(model="gpt-4o-mini")

prompt = ChatPromptTemplate(
    [
        SystemMessage(content=(
            "You are an assistant expert for parsing and saving receipt to xero"
            "Carefully analyze the receipt and use your knowledge on receipt to identify crucial components of receipts"
            "Focus on Line Items, Price, Qty, Tax, Tax Type and how they relate to each other for accurate calculation and identification"
            
            "Additional important instructions: \n"
            "1. 'TaxType' field: "
            "- Base the TaxType on this following fields: 'tax_rate', 'subtotal', 'total_tax', 'category'"
            "- Consider the given category/Account type of user to identify appropriate tax type, example receipt might be related to buying rathen than selling"
            "- Verify these pointers before saving to xero"
            "\n\n\n"
            

            "Format the output message in this ff format:"
            """
                Here’s a summary of the important details from your [name of bill] receipt. This breakdown highlights the key charges and payment information.

                [display here the very short summary of receipt, keep it 8 bullet points at most, list items purchased in bullet points, FInally compact the list]
                
                To help categorize this receipt properly, please choose a Category from the dropdown below.
            """

            "\n\n'Category' or 'Account' will be treated as the same" 
            "If account/category is given by user, use the tool provided to get more info before and automatically save the receipt to xero"
        )),
        MessagesPlaceholder(variable_name="chat_history"),
        MessagesPlaceholder(variable_name="input"),
        MessagesPlaceholder("agent_scratchpad"),
    ]
)

agent = create_openai_functions_agent(llm=model, tools=tools, prompt=prompt)
executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

def invoke(query: HumanMessage, memory: FileChatMessageHistory) -> AIMessage:
    parser = JsonOutputParser(pydantic_object=ReceiptLLM)

    response = executor.invoke({
        "input": [query],
        "chat_history": memory.messages,
        "jsonformat": parser.get_format_instructions()
    })

    ai_message = AIMessage(response["output"], id=random_alphanumeric())

    if query.additional_kwargs.get("attachment"):
        ai_message.response_metadata = {
            "category": "NOT_SET"
        }

    memory.add_message(ai_message)
    return ai_message


# img_type = ""
# image_base64 = ""

# message = HumanMessage(content=[
#     {"type": "image_url", "image_url": {"url": f"data:{img_type};base64,{image_base64}"}},
# ])

# assistant = invoke(
#     query=message, 
#     history=history_here
# )