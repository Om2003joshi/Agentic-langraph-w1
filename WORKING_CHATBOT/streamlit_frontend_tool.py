import streamlit as st
import uuid

from langgraph_tool_backend import chatbot, retrieve_all_threads

from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    ToolMessage,
)

# =========================
# Utilities
# =========================
def generate_thread_id():
    return str(uuid.uuid4())


def add_thread(thread_id):

    if thread_id not in st.session_state["chat_threads"]:
        st.session_state["chat_threads"].append(thread_id)


def reset_chat():

    thread_id = generate_thread_id()

    st.session_state["thread_id"] = thread_id

    add_thread(thread_id)

    st.session_state["message_history"] = []


def load_conversation(thread_id):

    state = chatbot.get_state(
        config={
            "configurable": {
                "thread_id": thread_id
            }
        }
    )

    return state.values.get("messages", [])


# =========================
# Session State
# =========================
if "message_history" not in st.session_state:
    st.session_state["message_history"] = []

if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = generate_thread_id()

if "chat_threads" not in st.session_state:
    st.session_state["chat_threads"] = retrieve_all_threads()

add_thread(st.session_state["thread_id"])

# =========================
# Sidebar
# =========================
st.sidebar.title("LangGraph Chatbot")

if st.sidebar.button("New Chat"):
    reset_chat()

st.sidebar.header("My Conversations")

for thread_id in st.session_state["chat_threads"][::-1]:

    if st.sidebar.button(str(thread_id)):

        st.session_state["thread_id"] = thread_id

        messages = load_conversation(thread_id)

        temp_messages = []

        for msg in messages:

            if isinstance(msg, HumanMessage):

                temp_messages.append({
                    "role": "user",
                    "content": msg.content
                })

            elif isinstance(msg, AIMessage):

                content = msg.content

                # Gemini structured response handling
                if isinstance(content, list):

                    final_text = ""

                    for item in content:

                        if isinstance(item, dict):

                            if item.get("type") == "text":
                                final_text += item.get("text", "")

                        elif isinstance(item, str):
                            final_text += item

                    content = final_text

                temp_messages.append({
                    "role": "assistant",
                    "content": content
                })

        st.session_state["message_history"] = temp_messages

# =========================
# Main UI
# =========================
st.title("🤖 LangGraph Chatbot")

# Render previous chat
for message in st.session_state["message_history"]:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])

# User input
user_input = st.chat_input("Type here...")

if user_input:

    # Store user message
    st.session_state["message_history"].append({
        "role": "user",
        "content": user_input
    })

    with st.chat_message("user"):
        st.markdown(user_input)

    CONFIG = {
        "configurable": {
            "thread_id": st.session_state["thread_id"]
        }
    }

    # Assistant response
    with st.chat_message("assistant"):

        status_holder = {"box": None}

        def ai_only_stream():

            for message_chunk, metadata in chatbot.stream(
                {"messages": [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode="messages",
            ):

                # Tool status
                if isinstance(message_chunk, ToolMessage):

                    tool_name = getattr(
                        message_chunk,
                        "name",
                        "tool"
                    )

                    if status_holder["box"] is None:

                        status_holder["box"] = st.status(
                            f"🔧 Using `{tool_name}`...",
                            expanded=True
                        )

                    else:

                        status_holder["box"].update(
                            label=f"🔧 Using `{tool_name}`...",
                            state="running",
                            expanded=True,
                        )

                # AI streaming
                if isinstance(message_chunk, AIMessage):

                    content = message_chunk.content

                    # Gemini structured output fix
                    if isinstance(content, list):

                        text_output = ""

                        for item in content:

                            if isinstance(item, dict):

                                if item.get("type") == "text":
                                    text_output += item.get("text", "")

                            elif isinstance(item, str):

                                text_output += item

                        yield text_output

                    else:

                        yield content

        ai_message = st.write_stream(ai_only_stream())

        # Complete tool status
        if status_holder["box"] is not None:

            status_holder["box"].update(
                label="✅ Tool finished",
                state="complete",
                expanded=False,
            )

    # Save assistant message
    st.session_state["message_history"].append({
        "role": "assistant",
        "content": ai_message
    })