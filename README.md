# Ellie-AI

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

## Quick Installation

### Option 1: Using the setup script (Recommended)

1. Run the setup script:
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

2. Start the web application:
   ```bash
   source venv/bin/activate
   python web_app.py
   ```

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

3. Run the setup script:
   ```bash
   python setup.py
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
   GROQ_API_KEY=your_actual_api_key_here
   ```

Note: The `.env` file contains sensitive information and is excluded from version control.

## Setting Up Course Materials

1. Create a directory for your course materials:
   ```bash
   mkdir -p course_materials/COURSE_ID
   ```
   Replace `COURSE_ID` with your course identifier (e.g., `CS101`, `MATH201`, etc.)

2. Add your course materials to the directory:
   ```bash
   cp path/to/materials/* course_materials/COURSE_ID/
   ```

## Usage

### Command Line Interface

Run the command line interface to interact with the AI Teaching Assistant:

```bash
python cli.py --course COURSE_ID
```

Replace `COURSE_ID` with your course identifier.

Available commands in the CLI:
- Type your question and press Enter to get an answer
- Type `update` to refresh course materials
- Type `exit` or `quit` to end the session

### Web Interface

Run the web application:

```bash
python web_app.py
```

Then open your browser and navigate to `http://localhost:5000`

The web interface allows you to:
1. Create new courses
2. Access existing courses
3. Ask questions through a chat interface
4. Update course materials with a single click

## How It Works

1. **Document Processing**: Course materials are loaded, processed, and split into chunks
2. **Vector Embedding**: Text chunks are converted to vector embeddings using a Hugging Face model
3. **Vector Storage**: Embeddings are stored in a FAISS vector database
4. **Retrieval**: When a question is asked, semantically similar text chunks are retrieved
5. **Generation**: The Groq LLM generates an answer based on the retrieved context

## Customization

### Environment Variables

You can customize the system by modifying the `.env` file:

```
GROQ_API_KEY=your_api_key_here
GROQ_MODEL=llama3-70b-8192   # Change to use a different Groq model
MATERIALS_DIR=course_materials   # Change to use a different directory for materials
```

### Advanced Configuration

For more advanced customization, you can modify the following parameters in `course_rag.py`:

- Chunk size and overlap for text splitting
- Number of documents to retrieve (top_k)
- Embedding model selection
- Prompt templates for the LLM

## Troubleshooting

- **Error: GROQ_API_KEY not found**: Ensure you've added your API key to the `.env` file
- **Empty responses**: Check that your course materials directory contains valid files
- **Slow performance**: Consider reducing the chunk size or number of documents retrieved

## License

[MIT License](LICENSE)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 
