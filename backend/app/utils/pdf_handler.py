"""
PDF handling utilities
"""
import os
from typing import Optional

try:
    import pdfplumber
except ImportError:
    pdfplumber = None


def extract_text_from_pdf(file_path: str) -> Optional[str]:
    """
    Extract text from PDF file
    
    Args:
        file_path: Path to PDF file
        
    Returns:
        str: Extracted text or None if error
    """
    if not pdfplumber:
        return None
    
    try:
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        
        return text.strip()
    except Exception as e:
        print(f"Error extracting PDF: {e}")
        return None


def get_relevant_pdf_context(pdf_text: str, question: str, max_chars: int = 2000) -> str:
    """
    Extract relevant context from PDF based on question
    
    Args:
        pdf_text: Full PDF text
        question: User's question
        max_chars: Maximum characters to return
        
    Returns:
        str: Relevant context from PDF
    """
    if not pdf_text:
        return ""
    
    # Split into paragraphs
    paragraphs = pdf_text.split("\n\n")
    
    # Find relevant paragraphs (simple keyword matching)
    question_words = set(question.lower().split())
    
    relevant_paragraphs = []
    for para in paragraphs:
        para_words = set(para.lower().split())
        # Count matching words
        matches = len(question_words & para_words)
        if matches > 0:
            relevant_paragraphs.append((para, matches))
    
    # Sort by relevance
    relevant_paragraphs.sort(key=lambda x: x[1], reverse=True)
    
    # Combine relevant paragraphs until we reach max_chars
    context = ""
    for para, _ in relevant_paragraphs:
        if len(context) + len(para) < max_chars:
            context += para + "\n\n"
        else:
            break
    
    return context.strip()