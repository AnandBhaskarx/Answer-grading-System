import os
import json
import google.generativeai as genai

def configure_gemini():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set.")
    genai.configure(api_key=api_key)

def evaluate_answer_sheet(student_file_paths, question_paper_paths, answer_key_paths, max_marks, passing_percentage):
    """
    Uploads the exam documents and student answer sheets to Gemini for multimodal OCR and grading.
    Returns a structured JSON dictionary containing the grading results.
    """
    configure_gemini()
    
    uploaded_files = []
    
    question_paper_paths = question_paper_paths or []
    answer_key_paths = answer_key_paths or []
    student_file_paths = student_file_paths or []
    
    try:
        print(f"Uploading files to Gemini API...")
        
        qp_files = []
        for path in question_paper_paths:
            f = genai.upload_file(path)
            qp_files.append(f)
            uploaded_files.append(f)
            
        ak_files = []
        for path in answer_key_paths:
            f = genai.upload_file(path)
            ak_files.append(f)
            uploaded_files.append(f)
            
        student_files = []
        for path in student_file_paths:
            f = genai.upload_file(path)
            student_files.append(f)
            uploaded_files.append(f)
        
        prompt = f"""
        You are an expert, strict, and highly accurate AI grading assistant.
        
        I have provided multiple files in this logical order:
        1. The Question Paper document(s).
        2. The Master Answer Key document(s).
        3. The handwritten or typed Answer Sheet(s) from a student.
        
        Your task is to:
        1. Read and understand the Question Paper and Master Answer Key.
        2. Perform OCR and visual understanding to read all pages of the student's answer sheet.
        3. Grade the student's answers accurately against the Master Answer Key.
        4. The maximum possible marks for this entire exam is {max_marks}.
        5. The passing percentage is {passing_percentage}%.
        
        Evaluate the exam question by question. Determine the appropriate marks to award based on the completeness and correctness of the student's answer relative to the master key.
        
        You MUST return ONLY a valid JSON object with the following schema:
        {{
            "total_score": float,
            "max_marks": {max_marks},
            "passed": boolean,
            "overall_feedback": "A brief summary of the student's performance.",
            "questions": [
                {{
                    "question_number": "1",
                    "student_answer_extracted": "The text you read from the image for this question",
                    "marks_awarded": float,
                    "max_marks_for_question": float,
                    "feedback": "Specific feedback on why marks were awarded or deducted."
                }}
            ]
        }}
        
        CRITICAL INSTRUCTION: Return ONLY the raw JSON string. Do not wrap it in ```json ... ``` markdown blocks.
        """
        
        # gemini-2.5-flash is extremely fast, highly capable in multimodal reasoning, and has a large context window.
        model = genai.GenerativeModel(
            model_name='gemini-2.5-flash',
            generation_config={"response_mime_type": "application/json"}
        )
        
        print("Sending generation request to Gemini 2.5 Flash...")
        # Pass the prompt and all the uploaded file objects
        contents = [prompt] + qp_files + ak_files + student_files
        response = model.generate_content(contents)
        
        response_text = response.text.strip()
        
        # Fallback cleanup just in case the model ignored the mime_type directive
        if response_text.startswith("```json"):
            response_text = response_text[7:-3].strip()
        elif response_text.startswith("```"):
            response_text = response_text[3:-3].strip()
            
        return json.loads(response_text)
        
    except Exception as e:
        print(f"Error in Gemini Evaluation: {e}")
        raise e
        
    finally:
        # Always clean up files from Google's temporary storage to prevent quota issues
        print("Cleaning up files from Gemini API...")
        for f in uploaded_files:
            try:
                genai.delete_file(f.name)
            except:
                pass
