import streamlit as st

with st.chat_message('user'):
    st.text('hi')
    
with st.chat_message('assistant'):
    st.text('how can i help you?')
    
with st.chat_message('user'):
    st.text('my name is om')
    
user_input = st.chat_input('type here')

if user_input :
    with st.chat_message('user'):
        st.text(user_input)