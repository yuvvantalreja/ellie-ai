# Ellie-AI (https://youtu.be/sQdA0E5u7ao)

<img width="1920" height="1024" alt="Screenshot 2025-08-08 at 11 31 35 PM" src="https://github.com/user-attachments/assets/ad772bd5-7e24-4c54-8e10-3191946d57ec" />

A powerful, customizable system designed to serve as an AI teaching assistant for university courses. It uses your course-specific materials to provide accurate, contextually relevant answers to student questions.

## Features

- **Course-Specific Knowledge**: Ellie has access to your material, so she gives answers that are relevent to you
- **Context-Aware Answers**: She uses RAG to retrieve relevant course content before answering
- **Searches the Web**: Ellie has access to the web. She is capable of providing up-to-date answers.
- **Multimodal Capabilities**: Ellie has eyes 👀
- **Document Processing**: Handles PDFs, DOCXs, TXTs, CSVs, and PowerPoint files
- **Easy Material Updates**: Update course materials without restarting the system

<img width="1920" height="1024" alt="Screenshot 2025-08-09 at 12 00 07 AM" src="https://github.com/user-attachments/assets/2618ae51-8623-4c5d-8e05-9c5617458545" />
<img width="1462" alt="Screenshot 2025-03-17 at 6 25 26 PM" src="https://github.com/user-attachments/assets/ac6ad80f-0e6a-4290-82d1-3d2809e41797" />
<img width="1420" height="1024" alt="Screenshot 2025-08-09 at 12 02 31 AM" src="https://github.com/user-attachments/assets/7a0b6813-6ad2-46c8-8e34-155d09ab14ab" />
<img width="1197" height="1001" alt="Screenshot 2025-08-09 at 12 08 59 AM" src="https://github.com/user-attachments/assets/53489c82-21d2-404f-addc-ad4e63af9812" />

## Prerequisites

- Python 3.8
- Groq API key (sign up at [groq.com](https://groq.com))
- Course materials in digital form (PDFs, DOCXs, etc.)

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```


2. Start the web application:
   ```bash
   python web_app.py
   ```

## Environment Setup

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file and add your Groq API key:
   ```
   GROQ_API_KEY=your_GROQ_API_KEY (Get this at https://console.groq.com/keys)
   TAVILY_API_KEY = your_TAVILY_API_KEY(OPTIONAL for Web Search) 
   ```


## How It Works

1. **Document Processing**: Course materials are loaded, processed, and split into chunks
2. **Vector Embedding**: Text chunks are converted to vector embeddings using an **all-MiniLM** Hugging Face model
3. **Vector Storage**: Embeddings are stored in a **FAISS** vector database
4. **Retrieval**: When a question is asked, semantically similar text chunks are retrieved
5. **Routing**: Routing LLM that decides what tool (RAG and/or web search) to use based on user query
6. **Generation**: The Groq LLM generates an answer based on the retrieved context


## Contributing

I'd love any new features ideas or additions! Just create a PR

Made with ❤️ in Pittsburgh
