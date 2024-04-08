import os
import panel as pn
import docx2txt  # For extracting text from DOCX
import PyPDF2  # For extracting text from PDF
import requests
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
import langchain.prompts as prompts
from panel.widgets.indicators import LoadingSpinner
import docx 
import pandas as pd
import time

 
# Define the HTML template
TEMPLATE = """
{% from macros import embed %}
 
<!DOCTYPE html>
<html lang="en">
{% block head %}
<head>
    {% block inner_head %}
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>LANE</title>
    {% block preamble %}{% endblock %}
    {% block resources %}
        {% block css_resources %}
        {{ bokeh_css | indent(8) if bokeh_css }}
        {% endblock %}
        {% block js_resources %}
        {{ bokeh_js | indent(8) if bokeh_js }}
        {% endblock %}
    {% endblock %}
    {% block postamble %}{% endblock %}
    {% endblock %}
</head>
{% endblock %}
{% block body %}
<style>
.bk-input-container{
width:95%
}
</style>
<body>
    <div class='chat-box' style="margin-top:8rem;border:1px solid black;background-color:#D1E8EA;margin-left: 18%; width: 60%;padding-bottom: 3rem;padding-top: 3rem;">
    {% block inner_body %}
    {% block contents %}
        {% for doc in docs %}
        {{ embed(doc) if doc.elementid }}
        {% for root in doc.roots %}
            {{ embed(root) | indent(10) }}
        {% endfor %}
        {% endfor %}
    {% endblock %}
    {{ plot_script | indent(8) }}
    {% endblock %}
    <div class='chat-box'>
</body>
{% endblock %}
</html>
"""
 
def create_app():
    input_style ={
         'margin': 'auto',
         'width': '60%',
         'padding': '10px',
         'color':'blue',
         'margin-top':'0.5rem',
         'padding':'5px'
        }
 
    button_style = {
        'text-align':'center',
        'margin-left' :'25rem'
    }
 
    prompt_style ={
        'margin': 'auto',
         'width': '50rem',
         'color':'blue',
         'margin-top':'0.5rem',
         'padding': '1rem'
 
        }
 
    prompt_text_style = {
    'color': 'black',
    'margin-top': '0.5rem',
    'width': '50rem',
    'margin': '0',
    'border': 'none',  # Corrected typo here
    'background': '#D1E8EA'
   }
 
    answer_style ={
         'margin': 'auto',
         'width': '50rem',
         'color':'red',
         'margin-top':'0.5rem',
         'padding': '0.5rem',
        }
 
    answer_text_style={
        'width': 'auto',
        'color':'black',
        'margin-top':'0.5rem',
        'margin-left':'1rem',
        'margin-right':'1rem',
        'width': '48rem'
    }
 
    spinner_style={
        'margin-left' :'25rem'
    }
 
    questions = pd.read_csv('questions.csv', encoding='UTF-8')

    upload_folder = "uploaded"
    os.makedirs(upload_folder, exist_ok=True)

    def save_uploaded_files(file_input, upload_folder):
        uploaded_files = file_input.filename
        # To store the paths of saved files
        saved_file_paths = []

        for uploaded_file in uploaded_files:
            if uploaded_file:
                # Process the uploaded document
                print(uploaded_files)
                print(upload_folder)
                file_path = os.path.join(upload_folder, uploaded_files)
                file_input.save(file_path)
                saved_file_paths.append(file_path)

        return saved_file_paths
 
    # Create a Select widget for the dropdown
    question_dropdown = pn.widgets.Select(options=['Select your question'] + questions['Questions'].tolist(),
             name='Select Question', styles=prompt_text_style)

    question_dropdown = pn.widgets.Select(
             name='Select Question', styles=prompt_text_style)
                                          
    file_input = pn.widgets.FileInput(width=300,styles=input_style,multiple=False)
    prompt = pn.widgets.TextInput(placeholder="Selected question will appear here...", styles=prompt_text_style)
    answer_text = pn.widgets.StaticText(value="Answer will appear here.",styles=answer_text_style)
    spinner = LoadingSpinner(value=True,width=50, height=50,visible=False,styles=spinner_style,color='primary',bgcolor='light')
    spinner_pane = pn.Row(spinner, width=50, height=50,styles=spinner_style)
 
 
    def update_prompt(event):
        selected_question = question_dropdown.value
        prompt.value = selected_question
        #prompt.value = prompt.value
 
    # Attach the update_prompt function to the question_dropdown's on_change event
    question_dropdown.param.watch(update_prompt, 'value')

    def upload_callback(event):
        spinner.visible = True
        saved_files = save_uploaded_files(file_input, upload_folder)
        print(f"Saved files: {saved_files}")
        spinner.visible = False

    file_input.param.watch(upload_callback, 'filename')
 
    def run_callback(event):
        # Show spinner while processing
        start_time = time.time()
        spinner.visible =True
        spinner.value = True
        spinner_pane[0] = spinner  # Ensure the widget is updated
 
        run_button.visible = False


 
 
        uploaded_file = file_input.filename
        print(uploaded_file)
 
        # for uploaded_file in uploaded_files:
        print("uploaded_files:",uploaded_file)
        if uploaded_file :
            print("uploaded_files:",uploaded_file)
            # Process the uploaded document
            if uploaded_file.endswith(('.docx')):
                upload_folder

                # Extract text from DOCX or TXT file
                text = docx2txt.process(upload_folder+ '/' + uploaded_file) if uploaded_file.endswith('.docx') else open(uploaded_file).read()
                print(text)
                question = prompt.value
                function_start_time = time.time()
                response = ask_question(question, text)
                function_end_time = time.time()
                function_time = function_end_time - function_start_time
                print("function time:",function_time)
                answer_text.value = response
                # Do something with the extracted text (e.g., store it, analyze it, etc.)
               
            elif uploaded_file.endswith('.pdf'):
                # Extract text from PDF file
                pdf_file = open(uploaded_file, 'rb')
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                text = ""
                for page_num in range(len(pdf_reader.pages)):
                    text += pdf_reader.pages[page_num].extract_text()
                pdf_file.close()

                # Do something with the extracted text (e.g., store it, analyze it, etc.)
                print(text)
                question = prompt.value
                response = ask_question(question, text)
                answer_text.value = response
            else:
                print(f"Unsupported file format for {uploaded_file}")

                # Process the question using an NLP service
             
 
        # Hide spinner after processing
        spinner.visible = False
        spinner_pane[0] = pn.Column()  # Hide the spinner
        run_button.visible = True
        end_time = time.time()
        total_time = end_time - start_time 
        print("total time:",total_time)
 
    run_button = pn.widgets.Button(name='Run', button_type='primary',styles=button_style)
    run_button.on_click(run_callback)
    widgets_question = pn.Row(
                            pn.Card(
                                    prompt,
                                  #  question_dropdown,
                                    title="Question"),
                            styles=prompt_style)
    widgets_answer = pn.Row(
                        pn.Card(
                            answer_text,
                            title="Answers"),
                    styles=answer_style)
    template = pn.Template(
        template=TEMPLATE,
        items={
            "file_input": file_input,
            "widgets_question": widgets_question,
            "widgets": widgets_answer,
            "run_button":  pn.Column(run_button),
            "spinner": spinner
        },
    )
    template.add_variable('title', 'Document Q&A App')
    return template
 
def ask_question(question, document_text):
    qa_prompt = prompts.PromptTemplate(
        input_variables=["question", "context_str", "length"],
        template="Imagine you are a Human Resource Manager."
                "Your task is to provide the detail accurate answer from the provided context."
                "Get me each answers with point wise"
                "Make sure to add the required words in the output."
                "Write an answer within ({length}) words for the question below based on the provided context. "
                "Try not to alter the content as much as possible."
                "The answer must be short and based on the question asked to you"
                "If provided context does not have sufficient information with regards to Question,Then reply 'Reference materials not located. Reformulate your question using the tips from the user guide for a precise answer.'"
                "Context: {context_str}\n"
                "Question: {question}\n"
                "Answer: ",
    )
    qa_chain = LLMChain(llm=ChatOpenAI(temperature=0.0, model_name='gpt-4-1106-preview',
                                      openai_api_key=''), prompt=qa_prompt)
    answer = qa_chain.run({"question": question, "context_str": document_text, "length": 80})
    return f'{answer}'
 
APP_ROUTES = {
    "LANE": create_app,
}
if __name__ == '__main__':
    pn.serve(APP_ROUTES, port=8086)