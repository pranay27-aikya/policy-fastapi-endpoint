import os, json
import PyPDF2 as pdf
from dotenv import load_dotenv
import google.generativeai as genai

from fastapi import FastAPI, UploadFile, File, Form

application = FastAPI()

# Load environment variables
load_dotenv()


@application.post("/upload_pdf/")
async def process_pdf(file: UploadFile = File(...)):
    # Ensure the file is a PDF
    if file.content_type != "application/pdf":
        return {"error": "Invalid file type. Please upload a PDF file."}
    print('pranay')
    # Configure Google Generative AI
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

    # Function to get response from Gemini Pro model
    def get_gemini_response(input_text):
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(input_text)
        return response.text

    # Function to extract text from PDF file
    def extract_text_from_pdf(uploaded_file):
        reader = pdf.PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text

    text = extract_text_from_pdf(file.file)
    input_prompt = f"""
        Act as a skilled insurance policy analyst. Your task is to read the given insurance policy and extract important information such as:
        - Name of the insurance holder
        - Name of the nominee
        - Insurance premium
        - Insurance coverage
        - Important driver clause
        - Limitations as to use

        Ensure to capture the entire content for each field.

        Insurance Policy:
        {text}

        Respond in a structured JSON format without any additional text:
        {{
            "Name of insurance holder": "",
            "Name of nominee": "",
            "Insurance premium": "",
            "Insurance coverage": "",
            "Important driver clause": "",
            "Limitations as to use": ""
        }}
    """
    response = get_gemini_response(input_prompt)

    if response.strip():  # Check if the response is not empty
        try:
            # Attempt to clean up the response if necessary
            cleaned_response = response.strip().replace("```", "").replace("json", "")
            extracted_info = json.loads(cleaned_response)
            return extracted_info
        except json.JSONDecodeError as e:
            return {'Error': 'Response received from llm was not valid JSON'}
    else:
        return {'Error': 'Received an empty response from the model. Please try again or contact support.'}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(application, host="0.0.0.0", port=8000)