# AI Teaching Assistant for University Courses

A powerful, customizable RAG (Retrieval-Augmented Generation) system designed to serve as an AI teaching assistant for university courses. It uses your course-specific materials to provide accurate, contextually relevant answers to student questions.

## Features

- **Course-Specific Knowledge**: Train the AI on your specific course materials
- **Context-Aware Answers**: Uses RAG to retrieve relevant course content before answering
- **Multiple Interfaces**: Command-line and web interfaces
- **Support for Multiple Courses**: Manage different courses with isolated knowledge bases
- **Document Processing**: Handles PDFs, DOCXs, TXTs, CSVs, and PowerPoint files
- **Easy Material Updates**: Update course materials without restarting the system

## Prerequisites

- Python 3.8 or higher
- Groq API key (sign up at [groq.com](https://groq.com))
- Course materials in digital form (PDFs, DOCXs, etc.)

## Installation

1. Clone this repository:
   ```bash
   git clone <your-repo-url>
   cd ai-teaching-assistant
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure your Groq API key:
   Edit the `.env` file and add your Groq API key:
   ```
   GROQ_API_KEY=your_api_key_here
   ```

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