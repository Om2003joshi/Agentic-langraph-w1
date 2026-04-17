import streamlit as st
from langraph_backend import chatbot
from langchain_core.messages import HumanMessage

# Config
CONFIG = {'configurable': {'thread_id': 'thread-1'}}

# Initialize session state
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

# Display previous messages
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])

# User input
user_input = st.chat_input('Type here')

if user_input:

    # Store user message
    st.session_state['message_history'].append({
        'role': 'user',
        'content': user_input
    })

    # Display user message
    with st.chat_message('user'):
        st.text(user_input)

    # Generate assistant response (streaming)
    with st.chat_message('assistant'):
        response_placeholder = st.empty()
        full_response = ""

        for message_chunk, metadata in chatbot.stream(
            {'messages': [HumanMessage(content=user_input)]},
            config=CONFIG,
            stream_mode="messages"
        ):
            if message_chunk.content:
                full_response += message_chunk.content
                response_placeholder.text(full_response)

    # Save assistant response
    st.session_state['message_history'].append({
        'role': 'assistant',
        'content': full_response
    })