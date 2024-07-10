import streamlit as st
import pandas as pd
import openai
import os
from dotenv import load_dotenv

load_dotenv()
# Set up the OpenAI API key
api_key = os.getenv('OPENAI_API_KEY')
openai.api_key = api_key

# Title for the Streamlit app
st.title("Excel Chatbot")

# Initialize session state for conversation history
if "conversation" not in st.session_state:
    st.session_state.conversation = []

# File upload for source and target Excel files
source_file = st.file_uploader("Upload the source Excel file", type=["xlsx"])
target_file = st.file_uploader("Upload the target Excel file", type=["xlsx"])

if source_file and target_file:
    # Read the uploaded Excel files
    source_df = pd.read_excel(source_file)
    target_df = pd.read_excel(target_file)

    # Check if the columns match
    if set(source_df.columns) == set(target_df.columns):
        st.success("Source and target file schema matched")
    else:
        st.error("Source and target file schema do not match")

    # Function to find mismatches between source and target dataframes
    def find_mismatches(source_df, target_df):
        mismatches = []
        common_columns = set(source_df.columns).intersection(set(target_df.columns))
        for column in common_columns:
            source_col = source_df[column]
            target_col = target_df[column]
            for idx, (source_val, target_val) in enumerate(zip(source_col, target_col)):
                if pd.isnull(source_val) and pd.isnull(target_val):
                    continue
                if source_val != target_val:
                    mismatches.append({
                        "column": column,
                        "index": idx,
                        "source_value": source_val,
                        "target_value": target_val
                    })
        return mismatches

    mismatches = find_mismatches(source_df, target_df)

    # Function to process user queries using OpenAI's GPT
    def answer_query(query, source_df, target_df, mismatches):
        source_dict = source_df.to_dict()
        target_dict = target_df.to_dict()
        detailed_prompt = f"""
        You are an advanced validation chatbot designed to compare two Excel sheets: a source file and a target file. Analyze the full contents of both files and the mismatch report to answer the user's query with precise values and explanations.
        Source Data: {source_dict}
        Target Data: {target_dict}
        Mismatch Report: {mismatches}
        User query: {query}
        """
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a highly sophisticated validation assistance designed to perform rigorous comparisons between the contents of corresponding columns in a source file and a target file. Analyze the two Excel files in their entirety and respond to the user's query, providing the response with the correct and accurate values. Conduct a thorough, cell-by-cell comparison of each column's contents between the source and target files. Maintain unwavering diligence throughout the comparison process, as accuracy is of paramount importance. Ensure that your comparison logic can handle large datasets efficiently without compromising accuracy. Approach each comparison with the utmost care and precision, as your analysis may inform important business decisions and processes. Be aware of and account for potential discrepancies such as leading/trailing whitespace, case sensitivity, and numerical precision. Maintain a neutral, objective tone in your reporting, focusing on facts and data rather than assumptions."},
                    {"role": "user", "content": detailed_prompt}
                ],
                max_tokens=1500,
                temperature=0.1
            )
            answer = response.choices[0].message['content'].strip()
            return answer
        except Exception as e:
            return f"An error occurred: {e}"

    # Function to generate follow-up questions based on the conversation history
    def generate_followup_question(conversation):
        conversation_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation])
        followup_prompt = f"""
        Based on the following conversation history, generate a relevant follow-up question for the user to keep the conversation going and gather more specific information:
        {conversation_history}
        """
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an assistant generating follow-up questions based on the conversation history."},
                    {"role": "user", "content": followup_prompt}
                ],
                max_tokens=1000,
                temperature=0.1
            )
            followup_question = response.choices[0].message['content'].strip()
            return followup_question
        except Exception as e:
            return f"An error occurred: {e}"

    # Streamlit interface for user queries
    st.write("## Conversation History")

    # Display conversation history
    for message in st.session_state.conversation:
        if message['role'] == 'user':
            st.write(f"**You:** {message['content']}")
        else:
            st.write(f"**Assistant:** {message['content']}")

    def clear_history():
        st.session_state.conversation = []  # Clear the conversation history

    st.button("Clear History", on_click=clear_history)

    def submit_query():
        user_query = st.session_state.user_query.strip()
        if user_query:
            # Store user query in conversation history
            st.session_state.conversation.append({"role": "user", "content": user_query})
            # Answer user query
            response = answer_query(user_query, source_df, target_df, mismatches)
            st.session_state.response = response
            # Append bot response to conversation history
            st.session_state.conversation.append({"role": "assistant", "content": response})
            # Generate follow-up question
            followup_question = generate_followup_question(st.session_state.conversation)
            st.session_state.conversation.append({"role": "assistant", "content": followup_question})

    st.write("## Ask your question")
    st.text_input("Enter your question about the Excel sheets:", key="user_query", on_change=submit_query)

    def clear_input():
        st.session_state.user_query = ""  # Clear the input box

    st.button("Clear", on_click=clear_input)
    st.write('## Additional Information')

    # Display the dataframes
    st.write("## Source Data")
    st.dataframe(source_df)
    st.write("## Target Data")
    st.dataframe(target_df)

else:
    st.write("Please upload both source and target Excel files to proceed.")
if __name__ == "__main__":
    import os
    os.system('streamlit run app.py')
