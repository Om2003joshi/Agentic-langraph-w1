from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
import os
import sqlite3

# Load environment variables
load_dotenv(override=True)

# LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.environ["GOOGLE_API_KEY"],
    temperature=0
)

# State
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# Node
def chat_node(state: ChatState):
    response = llm.invoke(state["messages"])
    return {"messages": [response]}

# SQLite connection
conn = sqlite3.connect("chatbot.db", check_same_thread=False)

# Checkpointer
checkpointer = SqliteSaver(conn=conn)

# Graph
graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_edge(START, "chat_node")
graph.add_edge("chat_node", END)

chatbot = graph.compile(checkpointer=checkpointer)

# Retrieve threads
def retrieve_all_threads():
    all_threads = set()
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config["configurable"]["thread_id"])
    return list(all_threads)