from langchain_core.messages import HumanMessage as Human



class HumanMessage(Human):
    additional_kwargs = {
        "metadata": {}
    }