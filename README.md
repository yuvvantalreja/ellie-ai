# Ellie-AI (https://ellie-ai.onrender.com/)

<img width="1470" alt="Screenshot 2025-03-17 at 6 24 07 PM" src="https://github.com/user-attachments/assets/dfb73b2b-6629-40f1-93f9-49228b412dc6" />

A powerful, customizable RAG (Retrieval-Augmented Generation) system designed to serve as an AI teaching assistant for university courses. It uses your course-specific materials to provide accurate, contextually relevant answers to student questions.

## Features

- **Course-Specific Knowledge**: Train the AI on your specific course materials

<img width="1470" alt="Screenshot 2025-03-17 at 6 24 55 PM" src="https://github.com/user-attachments/assets/0e9e57cd-8be0-4275-8f0d-3d99f6e409c9" />

- **Context-Aware Answers**: Uses RAG to retrieve relevant course content before answering

<img width="1462" alt="Screenshot 2025-03-17 at 6 25 26 PM" src="https://github.com/user-attachments/assets/ac6ad80f-0e6a-4290-82d1-3d2809e41797" />

- **Multiple Interfaces**: Command-line and web interfaces
- **Support for Multiple Courses**: Manage different courses with isolated knowledge bases

<img width="1470" alt="Screenshot 2025-03-17 at 6 24 16 PM" src="https://github.com/user-attachments/assets/e6c6f4aa-c6a1-48c1-a6df-36f620320215" />

- **Document Processing**: Handles PDFs, DOCXs, TXTs, CSVs, and PowerPoint files
- **Easy Material Updates**: Update course materials without restarting the system


## Prerequisites

- Python 3.8 or higher
- Groq API key (sign up at [groq.com](https://groq.com))
- Course materials in digital form (PDFs, DOCXs, etc.)

## Installation

### Option 2: Manual installation

1. Create a virtual environment (optional but recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```


4. Start the web application:
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
2. **Vector Embedding**: Text chunks are converted to vector embeddings using a Hugging Face model
3. **Vector Storage**: Embeddings are stored in a FAISS vector database
4. **Retrieval**: When a question is asked, semantically similar text chunks are retrieved
5. **Generation**: The Groq LLM generates an answer based on the retrieved context


## Contributing

I'd love any new features ideas or additions! Just create a PR

Made with ❤️ in Pittsburgh
