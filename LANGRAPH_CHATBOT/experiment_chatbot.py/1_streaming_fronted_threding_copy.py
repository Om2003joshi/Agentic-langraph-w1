import streamlit as st
from langraph_backend import chatbot
from langchain_core.messages import HumanMessage, AIMessage
import uuid

# **************************************** utility functions *************************

def generate_thread_id():
    return str(uuid.uuid4())   # ✅ always string

def generate_title(user_input):
    response = chatbot.invoke(
        {
            "messages": [
                HumanMessage(
                    content=f"Short title (max 5 words): {user_input}"
                )
            ]
        },
        config={
            "configurable": {
                "thread_id": "title-generator"
            }
        }
    )

    # ✅ extract last AI message
    messages = response["messages"]
    last_message = messages[-1]

    return last_message.content.strip().replace('"', '')

def add_thread(thread_id, title="New Chat"):
    if thread_id not in st.session_state['chat_threads']:
        # ✅ insert new chat at top
        st.session_state['chat_threads'] = {
            thread_id: title,
            **st.session_state['chat_threads']
        }

def reset_chat():
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    add_thread(thread_id)
    st.session_state['message_history'] = []

def load_conversation(thread_id):
    state = chatbot.get_state(config={'configurable': {'thread_id': thread_id}})
    return state.values.get('messages', [])


# **************************************** Session Setup ******************************

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = {}

add_thread(st.session_state['thread_id'])


# **************************************** Sidebar UI *********************************

st.sidebar.title('LangGraph Chatbot')

if st.sidebar.button('New Chat'):
    reset_chat()

st.sidebar.header('My Conversations')

for thread_id, title in st.session_state['chat_threads'].items():
    if st.sidebar.button(title, key=thread_id):   # ✅ FIXED (unique key)
        st.session_state['thread_id'] = thread_id

        # load previous messages
        messages = load_conversation(thread_id)

        temp_messages = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                role = 'user'
            else:
                role = 'assistant'

            temp_messages.append({
                'role': role,
                'content': msg.content
            })

        st.session_state['message_history'] = temp_messages


# **************************************** Main UI ************************************

# show chat history
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])

user_input = st.chat_input('Type here')

if user_input:

    # store user message
    st.session_state['message_history'].append({
        'role': 'user',
        'content': user_input
    })

    with st.chat_message('user'):
        st.text(user_input)

    CONFIG = {'configurable': {'thread_id': st.session_state['thread_id']}}

    # ✅ set title on first message
    if len(st.session_state['message_history']) == 1:
        title = generate_title(user_input)
        st.session_state['chat_threads'][st.session_state['thread_id']] = title

    # assistant response
    with st.chat_message("assistant"):
        def ai_only_stream():
            for message_chunk, metadata in chatbot.stream(
                {"messages": [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode="messages"
            ):
                if isinstance(message_chunk, AIMessage):
                    yield message_chunk.content

        ai_message = st.write_stream(ai_only_stream())

    # store assistant message
    st.session_state['message_history'].append({
        'role': 'assistant',
        'content': ai_message
    })