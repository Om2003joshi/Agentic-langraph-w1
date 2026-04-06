import streamlit as st 

message_history = []

user_input = st.chat_input('typed here')

if user_input:
    
    # first add the message to message_history
    message_history.append({'role':'user' , 'content' : 'user input'})
    with st.chat_message('user'):
        st.text(user_input)
        
   # first add the message to message_history
    message_history.append({'role':'assistant' , 'content' : 'user input'})
    with st.chat_message('assistant'):
        st.text(user_input)