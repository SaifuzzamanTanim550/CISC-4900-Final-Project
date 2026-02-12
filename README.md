# CISC-4900-Final-Project

Senior project for CISC 4900 – research, code, experiments, and documentation.

---

## Project Overview

This project is an AI-based document assistant that helps generate email responses using official documents and templates.

The main use case is for the Brooklyn College Undergraduate Admissions Office. Staff answer more than 50 emails per day, and many of them are repetitive FAQs. Currently, they manually search documents, copy sections, and edit responses. This takes time and can lead to small mistakes during busy periods.

This system aims to reduce that repetition by retrieving the correct information from documents and generating a grounded draft response.

---

## Problem

Admissions staff currently:

- Manually search through policy documents and templates
- Use Ctrl + F to find answers
- Copy and paste responses
- Edit wording for each email

This process is repetitive and time consuming.

The goal is not to create new content.  
The goal is to quickly find approved information and turn it into a consistent draft response.

---

## Solution

This project follows a retrieval-based approach:

1. Upload and read documents
2. Split documents into sections
3. Rank sections using BM25
4. Use a Hugging Face model to select the best matching section
5. Generate a draft response based only on the retrieved content

If the system cannot find enough support in the documents, it will not guess. It will notify the user instead.

---

## Tech Stack

Backend:
- Python

Frontend:
- Streamlit (Python-based web app)

Tools and Technologies:
- Hugging Face Inference API
- MongoDB (document storage and chat history)
- rank-bm25
- GitHub

---

## Current Status

- Prototype built in Google Colab
- DOCX document support
- BM25 retrieval working
- LLM-based template selection
- Draft response generation

---

## Next Steps

- Improve retrieval using embeddings and vector search
- Add better conversation memory
- Deploy fully using Streamlit

---

## Author

Saifuzzaman Tanim  
CISC 4900 – Spring 2026  
Brooklyn College
