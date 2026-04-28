import streamlit as st
from langraph_backend import chatbot
from langchain_core.messages import HumanMessage
import uuid

# ******************************************** utility functions ***********************************************
def generate_thread_id():
    return str(uuid.uuid4())   # convert to string (important)

def add_thread(thread_id):
    if thread_id not in st.session_state['chat_thread']:
        st.session_state['chat_thread'].append(thread_id)

def reset_chat():
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    add_thread(thread_id)
    st.session_state['message_history'] = []

# ******************************************** Session Setup ***********************************************
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_thread' not in st.session_state:
    st.session_state['chat_thread'] = []

# add current thread safely
add_thread(st.session_state['thread_id'])

# ******************************************** Sidebar UI *************************************************
st.sidebar.title("Langraph Chatbot")

if st.sidebar.button("New Chat"):
    reset_chat()

st.sidebar.header("My conversations")

for thread_id in st.session_state['chat_thread']:
    if st.sidebar.button(thread_id):
        st.session_state['thread_id'] = thread_id
        st.session_state['message_history'] = []   # (optional: later you can load history)

# ******************************************** Main UI *************************************************
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

    # assistant response
    with st.chat_message('assistant'):
        ai_message = st.write_stream(
            message_chunk.content
            for message_chunk, metadata in chatbot.stream(
                {'messages': [HumanMessage(content=user_input)]},
                config={'configurable': {'thread_id': st.session_state['thread_id']}},
                stream_mode='messages'
            )
        )

    # store assistant message
    st.session_state['message_history'].append({
        'role': 'assistant',
        'content': ai_message
    })