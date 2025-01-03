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

def random_alphanumeric(length=10):
    """Generate a random alphanumeric string."""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=length))


@tool
def save_receipt_to_xero(receipt: ReceiptLLM) -> str:
    """This tool accepts receipt data and save to xero"""

    try:

        line_items = [item.as_xero() for item in receipt.line_items]

        receipts = {
            "Receipts": [
                {
                    "Date": receipt.date,
                    "LineItems": line_items,
                    "Contact": {
                        "ContactID": config.contact_id
                    },
                    "User": {
                        "UserID": config.user_id
                    },
                    "LineAmountTypes": receipt.line_amount_types,
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
            "If image url is included in user input, parse it very specific instruction and schema below:\n"
            "Receipts might not always provide the Unit amount and Line amount," 
            "Always refer to overall total and tax, calculate the list items and compare to determine whether the item price is unit or line amount"
            "That will prevent instances where prices are doubled when quantity is 2 or more" 
            "Majority of the time the price displayed is line amount, in that case leave the unit price as empty value, vice versa"
            "Analyze the computation overall to properly fill the values, accuracy is important here"
            "Additionaly, make sure to add other fees except Taxes as ListItem for example 'Admin Fee', 'Tips' etc."
            "Additionally, any fees (e.g., 'Admin Fee', 'Tips') should be treated as list items and should always have a unit amount with quantity 1."
            "Do not include tax in the list items. Ensure that additional fees are not mistakenly included in the tax total.\n\n"
            "The tax total will always explicitly mention that it is tax, so do not get confused.\n\n"
            
            "Carefully analyze the entire receipt and map the information to the following schema. "
            "Use this format:\n"
            "{jsonformat}"
            "\n\n\n"
            

            "Format the output message in this ff format:"
            """
                Here’s a summary of the important details from your [name of bill] receipt. This breakdown highlights the key charges and payment information.

                [display here the only needed details in bullet points (not very detailed)]
                
                To help categorize this receipt properly, please choose a Category from the dropdown below.
            """
            "'Category' or 'Account' will be treated as the same" 
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

    if isinstance(query.content, list):
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