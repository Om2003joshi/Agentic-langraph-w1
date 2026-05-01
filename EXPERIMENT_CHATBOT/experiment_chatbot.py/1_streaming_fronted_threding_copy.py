import streamlit as st
from langraph_backend import chatbot, retrieve_all_threads, llm
from langchain_core.messages import HumanMessage, AIMessage
import uuid

# ================= Utility =================

def generate_thread_id():
    return str(uuid.uuid4())

# ✅ FIXED: No LangGraph usage (no DB pollution)
def generate_title(user_input):
    response = llm.invoke(
        f"""
        Generate a single short title (max 5 words) for this message.

        Rules:
        - Only one title
        - No symbols (*, -, bullets)
        - No explanations
        - Plain text only

        Message: {user_input}
        """
    )

    title = response.content.strip().replace('"', '').replace('*', '')

    # fallback safety
    return title.split("\n")[0]

# ✅ FIXED: Better default name
def add_thread(thread_id, title=None):
    if thread_id not in st.session_state['chat_threads']:
        if title is None:
            title = f"Chat {len(st.session_state['chat_threads']) + 1}"

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
    state = chatbot.get_state(
        config={'configurable': {'thread_id': thread_id}}
    )
    return state.values.get('messages', [])

# ================= Session Setup =================

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

# ✅ FIXED: Load from DB
if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = {}

    for thread_id in retrieve_all_threads():
        st.session_state['chat_threads'][thread_id] = "Previous Chat"

add_thread(st.session_state['thread_id'])

# ================= Sidebar =================

st.sidebar.title('LangGraph Chatbot')

if st.sidebar.button('New Chat'):
    reset_chat()

st.sidebar.header('My Conversations')

for thread_id, title in st.session_state['chat_threads'].items():
    if st.sidebar.button(title, key=thread_id):
        st.session_state['thread_id'] = thread_id

        messages = load_conversation(thread_id)

        temp_messages = []
        for msg in messages:
            role = 'user' if isinstance(msg, HumanMessage) else 'assistant'
            temp_messages.append({
                'role': role,
                'content': msg.content
            })

        st.session_state['message_history'] = temp_messages

# ================= Main UI =================

# Show chat history
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])

user_input = st.chat_input('Type here')

if user_input:

    # ✅ FIXED: detect first message BEFORE append
    is_first_message = len(st.session_state['message_history']) == 0

    # store user message
    st.session_state['message_history'].append({
        'role': 'user',
        'content': user_input
    })

    with st.chat_message('user'):
        st.text(user_input)

    CONFIG = {
        'configurable': {
            'thread_id': st.session_state['thread_id']
        }
    }

    # ✅ FIXED: correct title logic
    if is_first_message:
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
                if isinstance(message_chunk, AIMessage) and message_chunk.content:
                    yield message_chunk.content

        ai_message = st.write_stream(ai_only_stream())

    # store assistant message
    st.session_state['message_history'].append({
        'role': 'assistant',
        'content': ai_message
    })