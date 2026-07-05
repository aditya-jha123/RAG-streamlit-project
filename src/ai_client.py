# src/ai_client.py
import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

# Initialize the Gemini Client
client = genai.Client()

def review_code_with_rag(code_content, retrieved_rules=""):
    """
    Sends the code and any retrieved RAG guidelines to the Gemini API.
    """
    # If we have custom rules from ChromaDB, we append them to the prompt
    rules_context = ""
    if retrieved_rules:
        rules_context = f"\nYou must prioritize checking the code against these specific organizational rules:\n{retrieved_rules}\n"

    prompt = f"""
    You are an expert Senior Software Engineer. Review the following code snippet for logic errors, security flaws, style guidelines, and performance bottlenecks.
    {rules_context}
    
    Code to review:
    ```python
    {code_content}
    ```
    
    Provide your review with clear markdown headings, constructive feedback, and fixed code snippets where necessary.
    """
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
    )
    return response.text

# We comment out or remove the direct execution text down here 
# so it doesn't accidentally run when we import this file later!
if __name__ == "__main__":
    test_code = "def add_nums(a, b): pass"
    print("Testing AI Client locally...")
    print(review_code_with_rag(test_code))