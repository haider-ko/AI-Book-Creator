# Import necessary libraries
import os
import streamlit as st
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from langchain_community.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from fpdf import FPDF
import PyPDF2

# Load environment variables from .env file
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

# Initialize the model
model = ChatOpenAI(model="gpt-3.5-turbo-1106",
                   temperature=0.7)

# Set Streamlit page configuration
st.set_page_config(page_title='🤖Book Creator', layout='wide')

# Set up the Streamlit app layout
st.title("Book Creator")
st.subheader("Your personal book creating assistant")
st.markdown(
    "Fill the form in the sidebar to generate your book or upload a PDF to edit it!")

# Sidebar form for user input
with st.sidebar:
    # Book generation form
    with st.form("book_form"):
        theme = st.text_input("Theme")
        intro = st.text_input("General Introduction")
        pages = st.number_input("Number of Pages", min_value=1, step=1)
        book_type = st.text_input("Type of Article (Romance, Thriller, etc)")
        generate_button = st.form_submit_button("Generate")

    # PDF editing form
    uploaded_pdf = st.file_uploader("Upload a PDF to edit", type=["pdf"])
    edit_instruction = st.text_input("Specify what to edit in the PDF")
    edit_button = st.button("Edit PDF")

prompt_template = """
You are a highly creative and skilled novelist, known for crafting engaging and riveting stories across various genres such as romance, thriller, fantasy, and more. Your task today is to generate a complete book based on the details provided by the user.

The user will provide you with the following details:
- Theme: {theme}
- General Introduction: {intro}
- Number of Pages: {pages}
- Type of Book (Romance, Thriller, etc): {type}

Please ensure the book you create is cohesive, compelling, and aligns with the user's provided information. Your story should captivate readers from start to finish, keeping in mind the genre specifications and desired length.

In your writing, remember to:
- Develop vibrant and relatable characters with unique personalities and motivations.
- Structure the plot with a clear beginning, middle, and end, including significant turning points and climax.
- Incorporate intricate plot twists to maintain intrigue and suspense throughout the story.
- Create an immersive narrative that resonates with the chosen theme and genre, making readers eager to turn the next page.

Aim to provide an immersive reading experience that transports the reader into the world you create. Let your creativity flow and produce a story that leaves a lasting impression on the reader.
"""

# Create the prompt and parser
prompt = ChatPromptTemplate.from_template(prompt_template)
parser = StrOutputParser()

# Chain to invoke the model
chain = LLMChain(prompt=prompt, llm=model, output_parser=parser)

# Handle the user input and generate a response
if generate_button and theme and intro and pages and book_type:
    with st.spinner("Generating the book outline..."):
        response = chain.invoke({
            "theme": theme,
            "intro": intro,
            "pages": pages,
            "type": book_type,
        })
        st.session_state.response = response['text']
        st.success("Here is your book outline:")
        st.write(st.session_state.response)

# Generate PDF only if response is available
if 'response' in st.session_state:
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 12)
            self.cell(0, 10, 'Book Outline', 0, 1, 'C')

        def chapter_title(self, chapter_title):
            self.set_font('Arial', 'B', 12)
            self.cell(0, 10, chapter_title, 0, 1, 'L')

        def chapter_body(self, body):
            self.set_font('Arial', '', 12)
            self.multi_cell(0, 10, body)

        def add_chapter(self, chapter_title, body):
            self.add_page()
            self.chapter_title(chapter_title)
            self.chapter_body(body)

    pdf = PDF()

    # Adding title and introduction
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'Book Outline', 0, 1, 'C')
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f"Theme: {theme}", 0, 1)
    pdf.cell(0, 10, f"Introduction: {intro}", 0, 1)
    pdf.cell(0, 10, f"Number of Pages: {pages}", 0, 1)
    pdf.cell(0, 10, f"Type: {book_type}", 0, 1)
    pdf.ln(10)

    # Adding generated outline
    pdf.set_font('Arial', '', 12)
    pdf.multi_cell(0, 10, st.session_state.response)

    # Save the PDF to a file
    pdf_output_path = "book_outline.pdf"
    pdf.output(pdf_output_path)

    # Provide a download link in Streamlit
    with open(pdf_output_path, "rb") as pdf_file:
        st.download_button(
            label="Download PDF",
            data=pdf_file,
            file_name="book_outline.pdf",
            mime="application/pdf",
        )

# Handle PDF editing
if edit_button and uploaded_pdf and edit_instruction:
    # Extract text from the uploaded PDF
    reader = PyPDF2.PdfReader(uploaded_pdf)
    pdf_text = ""
    for page in reader.pages:
        pdf_text += page.extract_text()

    st.session_state.pdf_text = pdf_text

    # Define the editing prompt template
    edit_prompt_template = """
    You’re an editor, and your task today is to edit the content provided by the user to improve its readability, coherence, and overall quality.

    The user has uploaded a PDF with the following content:
    {pdf_text}

    The user wants to edit the following:
    {edit_instruction}

    Edit the content accordingly to make it more engaging and polished.
    """

    # Create the editing prompt and parser
    edit_prompt = ChatPromptTemplate.from_template(edit_prompt_template)
    edit_chain = LLMChain(prompt=edit_prompt, llm=model, output_parser=parser)

    # Generate the edited response
    with st.spinner("Editing the PDF content..."):
        edited_response = edit_chain.invoke({
            "pdf_text": pdf_text,
            "edit_instruction": edit_instruction
        })
        st.session_state.edited_response = edited_response['text']
        st.success("Here is your edited PDF content:")
        st.write(st.session_state.edited_response)

# Generate PDF with edited content
if 'edited_response' in st.session_state:
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 12)
            self.cell(0, 10, 'Edited PDF Content', 0, 1, 'C')

        def chapter_title(self, chapter_title):
            self.set_font('Arial', 'B', 12)
            self.cell(0, 10, chapter_title, 0, 1, 'L')

        def chapter_body(self, body):
            self.set_font('Arial', '', 12)
            self.multi_cell(0, 10, body)

        def add_chapter(self, chapter_title, body):
            self.add_page()
            self.chapter_title(chapter_title)
            self.chapter_body(body)

    edited_pdf = PDF()

    # Adding edited content
    edited_pdf.add_page()
    edited_pdf.set_font('Arial', 'B', 16)
    edited_pdf.cell(0, 10, 'Edited PDF Content', 0, 1, 'C')
    edited_pdf.ln(10)
    edited_pdf.set_font('Arial', '', 12)
    edited_pdf.multi_cell(0, 10, st.session_state.edited_response)

    # Save the edited PDF to a file
    edited_pdf_output_path = "edited_pdf_content.pdf"
    edited_pdf.output(edited_pdf_output_path)

    # Provide a download link in Streamlit
    with open(edited_pdf_output_path, "rb") as pdf_file:
        st.download_button(
            label="Download Edited PDF",
            data=pdf_file,
            file_name="edited_pdf_content.pdf",
            mime="application/pdf",
        )

# Debugging prints
print("Theme:", theme)
print("Intro:", intro)
print("Pages:", pages)
print("Type:", book_type)
print("Response:", st.session_state.response if 'response' in st.session_state else "No response generated")
print("Edited Response:", st.session_state.edited_response if 'edited_response' in st.session_state else "No edited response generated")
