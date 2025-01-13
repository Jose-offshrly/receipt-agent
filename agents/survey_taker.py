
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

import uuid, json
from langchain_openai.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_community.chat_message_histories import ChatMessageHistory
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain.agents import create_openai_functions_agent, AgentExecutor 
from langchain_core.output_parsers import PydanticOutputParser

system_prompt = """
        You are a survey conductor agent. Given a predefined series of question, You conduct survey to employees.

        You conduct the survey with this following guidelines.
        1. Using the survey info given below, ask the employee a question one at a time
        2. If user has clarification with the current question, answer it.
        3. The only valid answer to each item is one of the following: Very Satisfied, Satisfied, Neutral, Dissatisfied, Very Dissatisfied
        4. The survey will only finish if all questions are answered. Use the tool given to you to save the survey
        5. The survey start if you received --START-- flag
        6 Survey data provided is already formatted and ensured to adhere this schema: {survey_schema} 
        \n\n

        Here's the survey data that you will be conducting to the employees.\n
        {survey_data}

        \n\n

        Instruction for rendering the question
        1. Use the template for rendering each survey question.
        2. Note that its important to add "--SELECT_ANSWER--" in the end of every survey question for tracking purposes and will be used later on. 
        3. Do not add anything else in your response, Align you answer in given format at all times.
        4. Do not add any other information in response

        Survey Question Format:\n

        **[item no.]. [first question here]?**--SELECT_ANSWER--
        
        \nExample: \n

        **1. Are you satisfied with the length of your break times during work hours?**--SELECT_ANSWER--
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


class Survey(BaseModel):
    survey_about: str = Field(description="The topic which the survey is about")
    questions: list[Question] = Field(description="The questions list included in survey")

class Progress(BaseModel):
    question: str = Field(description="The current question answered by user")
    answer: str = Field(description="The employee answer to the survey question")


@tool(args_schema=Progress)
def save_progress_of_survey(question: str, answer: str):
    """This tool is responsible for saving the progress of survey. Call this each time employee answer a question"""

    print(f"Survey progress save: \n Question: {question} \n Answer: {answer}")
    return "progress save"

tools = [save_progress_of_survey]
model = ChatOpenAI(model="gpt-4o")
parser = PydanticOutputParser(pydantic_object=Survey)

agent = create_openai_functions_agent(llm=model, tools=tools, prompt=prompt)
executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
SUFFIX_ID_FOR_CTA = "--SELECT_ANSWER--"


def load_sample_data():
    path = "data/sample_survey.json"

    with open(path, "r") as f:
        data = json.load(fp=f)
        return data
    


def invoke(query: HumanMessage, memory: ChatMessageHistory):
    print("query", query)

    survey_data_str = json.dumps(load_sample_data())

    response = executor.invoke({
        "input": query.content,
        "chat_history": memory.messages,
        "survey_data": survey_data_str,
        "survey_schema": parser.get_format_instructions()
    })

    ai_message = AIMessage(response["output"], id=str(uuid.uuid4()))
    ai_message.additional_kwargs.setdefault("metadata", {})

    if ai_message.content.strip().endswith(SUFFIX_ID_FOR_CTA):
        ai_message.additional_kwargs["metadata"] = {
            "agent": "take_survey",
            "response_type": "survey_question"
        }

    memory.add_message(query)
    memory.add_message(ai_message)
    return ai_message
