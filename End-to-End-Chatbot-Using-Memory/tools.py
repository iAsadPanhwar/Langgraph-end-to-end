from dotenv import load_dotenv
import os
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.graph.message import add_messages
from typing import Annotated, TypedDict, Literal
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode


load_dotenv()

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

@tool
def search(query: str):
    """this is my costum tool"""
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degree and foggy"
    return "It's 90 degrees and sunny."

print(search.invoke("What is temperature in sf?"))

tool_node = ToolNode([search])
llm_with_tools = llm.bind_tools([search])
def call_model(state: MessagesState):
    messages = state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages":[response]}

def router_function(state: MessagesState) -> Literal["tools",END]:
    messages = state["messages"]
    last_message = messages[-1]

    if last_message.tool_calls:
        return "tools"
    return END

workflow = StateGraph(MessagesState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)

workflow.add_edge(START, "agent")

workflow.add_conditional_edges("agent",router_function,{"tools":"tools", END:END})

app=workflow.compile()

input = {"messages":["Hi how are you?"]}

# app.invoke(input)

for output in app.stream(input):
    for key,value in output.items():
        print(f"Output from {key} Node")
        print("==========")
        print(value)
        print("\n")
