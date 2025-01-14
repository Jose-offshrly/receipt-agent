
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

import uuid
from langchain_openai.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_community.chat_message_histories import ChatMessageHistory
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain.agents import create_openai_functions_agent, AgentExecutor 

system_prompt = """
        You are a survey form generator. Create a form based on the following requirements:

        1. The form should follow a clean, modern design with consistent spacing and alignment
        2. Each question should have 5 satisfaction levels: Very Satisfied, Satisfied, Neutral, Dissatisfied, Very Dissatisfied
        3. Use a purple color scheme (#6C47FF for primary actions)
        4. Make it clean and readable\n\n

        Generation of survey question instructions:\n
        1. Generate atleast 10 or more survey questions that is related to topic given by user at all times. Make sure that you cover all aspects so that management can gather as much as info to the employee
        2. Make sure the question is relevant and helpful. Remember that your purpose for creating survey is to help the employee and the company assess the raised concern. So that the management can come up with solution
        3. User is expected to add one question at a time unless specified in the query, add only one
        4. Always return the whole updated form in your response\n\n

        Example:\n
        Topic raised: "Working hours"
        Questions:
        - How satisfied are you with your current working hours?
        - Do you feel satisfied about your current work-life balance?

        \n\nAdditional requirements:
        - Each question should be in its own container with horizontal actions directly below it
        - Options should be horizontally aligned buttons\n\n

        Importtant!: Always output the form in this exact template: \n\n
      
        **[You're friendly response to the user, maximum of one sentence. Example Certainly!, Here's a Employee Survey on Working Hours to help gauge your team's opinions and satisfaction]**
        
        ---
        
        **1. [first question here]?**

        <div style="display: flex; justify-content: space-around; margin-bottom: 10px;">
        <button style="border: 2px solid #6C47FF; background: white; color: #6C47FF; border-radius: 5px; padding: 5px; padding-left: 10px; padding-right: 10px;">Very Satisfied</button>
        <button style="border: 2px solid #6C47FF; background: white; color: #6C47FF; border-radius: 5px; padding: 5px; padding-left: 10px; padding-right: 10px;">Satisfied</button>
        <button style="border: 2px solid #6C47FF; background: white; color: #6C47FF; border-radius: 5px; padding: 5px; padding-left: 10px; padding-right: 10px;">Neutral</button>
        <button style="border: 2px solid #6C47FF; background: white; color: #6C47FF; border-radius: 5px; padding: 5px; padding-left: 10px; padding-right: 10px;">Dissatisfied</button>
        <button style="border: 2px solid #6C47FF; background: white; color: #6C47FF; border-radius: 5px; padding: 5px; padding-left: 10px; padding-right: 10px;">Very Dissatisfied</button>
        </div>

        **1. [second question here]?**

        <div style="display: flex; justify-content: space-around; margin-bottom: 10px;">
        <button style="border: 2px solid #6C47FF; background: white; color: #6C47FF; border-radius: 5px; padding: 5px; padding-left: 10px; padding-right: 10px;">Very Satisfied</button>
        <button style="border: 2px solid #6C47FF; background: white; color: #6C47FF; border-radius: 5px; padding: 5px; padding-left: 10px; padding-right: 10px;">Satisfied</button>
        <button style="border: 2px solid #6C47FF; background: white; color: #6C47FF; border-radius: 5px; padding: 5px; padding-left: 10px; padding-right: 10px;">Neutral</button>
        <button style="border: 2px solid #6C47FF; background: white; color: #6C47FF; border-radius: 5px; padding: 5px; padding-left: 10px; padding-right: 10px;">Dissatisfied</button>
        <button style="border: 2px solid #6C47FF; background: white; color: #6C47FF; border-radius: 5px; padding: 5px; padding-left: 10px; padding-right: 10px;">Very Dissatisfied</button>
        </div>

        --NOTIFY_SECTION_HERE--

        \n\n

        The expects that template to make the application work
        Always include the "--NOTIFY_SECTION_HERE--" at the bottom of survery form, it will be use later at application level

    """


prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    MessagesPlaceholder(variable_name="chat_history"),
    ("user", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad")
])

class Question(BaseModel):
    question_number: int = Field(description="The incremental survey question number")
    question: str = Field(description="The survey question")


class SurveyForm(BaseModel):
    survey_about: str = Field(description="The topic which the survey is about")
    questions: list[Question] = Field(description="The questions list included in survey")

@tool
def save_survey_and_notify_employees(survey: SurveyForm):
    """This tool is responsible for saving the generated survey and notifying the employees"""

    print("Survey sent to employees")
    print(survey.model_dump())

tools = [save_survey_and_notify_employees]
model = ChatOpenAI(model="gpt-4o")

agent = create_openai_functions_agent(llm=model, tools=tools, prompt=prompt)
executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
SUFFIX_ID_FOR_CTA = "--NOTIFY_SECTION_HERE--"


def invoke(query: HumanMessage, memory: ChatMessageHistory):
    
    response = executor.invoke({
        "input": query.content,
        "chat_history": memory.messages
    })

    ai_message = AIMessage(response["output"], id=str(uuid.uuid4()))

    if ai_message.content.strip().endswith(SUFFIX_ID_FOR_CTA):
        ai_message.content = ai_message.content.strip()[:-len(SUFFIX_ID_FOR_CTA)]
        ai_message.additional_kwargs.setdefault("metadata", {})["metadata"] = {
            "agent": "survey",
            "response_type": "survey"
        }

    memory.add_message(query)
    memory.add_message(ai_message)
    return ai_message
