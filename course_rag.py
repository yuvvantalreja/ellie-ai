import os
import pickle
import logging
from typing import Dict, List, Optional, Tuple, Any
from dotenv import load_dotenv

# LangChain imports
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    Docx2txtLoader,
    CSVLoader,
    UnstructuredPowerPointLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.documents import Document

# PDF and document processing
import fitz  # PyMuPDF
from pptx import Presentation
import re
import hashlib
import pathlib

# Import new components
from conversation_manager import ConversationManager
from course_prompts import CoursePromptManager
from feedback_system import FeedbackSystem

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CourseRAG:
    """RAG system for university course materials using Groq API"""
    
    def __init__(self, course_id: str, materials_dir: Optional[str] = None,
                discipline: Optional[str] = None):
        """Initialize the RAG system for a specific course
        
        Args:
            course_id: Identifier for the course (e.g., "CS101")
            materials_dir: Directory containing course materials (optional)
            discipline: Course discipline for prompt templates (optional)
        """
        self.course_id = course_id
        self.materials_dir = materials_dir or os.getenv("MATERIALS_DIR", "course_materials")
        self.course_dir = os.path.join(self.materials_dir, course_id)
        self.vectorstore_dir = "vectorstores"
        self.vectorstore_path = os.path.join(self.vectorstore_dir, f"{course_id}_vectorstore.pkl")
        self.discipline = discipline
        
        # Initialize embeddings
        self.embeddings = self._create_embeddings()
        
        # Initialize vector store
        self.vectorstore = self._initialize_vectorstore()
        
        # Initialize LLM
        self.llm = self._initialize_llm()
        
        # Initialize conversation manager
        self.conversation_manager = ConversationManager()
        
        # Initialize prompt manager
        self.prompt_manager = CoursePromptManager()
        
        # Initialize feedback system
        self.feedback_system = FeedbackSystem()
        
        # Build the RAG chain
        self.rag_chain = self._build_rag_chain()
    
    def _create_embeddings(self):
        """Create embeddings using a local HuggingFace model"""
        logger.info("Initializing embeddings model...")
        return HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
    
    def _initialize_llm(self):
        """Initialize the Groq LLM"""
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        
        model_name = os.getenv("GROQ_MODEL", "llama3-70b-8192")
        logger.info(f"Initializing Groq LLM with model: {model_name}")
        
        return ChatGroq(
            api_key=groq_api_key,
            model_name=model_name
        )
    
    def _load_documents(self):
        """Load all documents from the course materials directory"""
        logger.info(f"Loading documents for course {self.course_id}")
        
        documents = []
        course_dir = os.path.join(self.materials_dir, self.course_id)
        
        if not os.path.exists(course_dir):
            logger.warning(f"Course directory not found: {course_dir}")
            return []
        
        for root, _, files in os.walk(course_dir):
            for file in files:
                file_path = os.path.join(root, file)
                file_ext = os.path.splitext(file)[1].lower()
                
                try:
                    if file_ext == '.pdf':
                        # Extract metadata like titles and page numbers
                        pdf_docs = self._load_pdf_with_metadata(file_path)
                        documents.extend(pdf_docs)
                    elif file_ext == '.pptx':
                        # Extract metadata like slide numbers and titles
                        ppt_docs = self._load_pptx_with_metadata(file_path)
                        documents.extend(ppt_docs)
                    elif file_ext == '.txt':
                        loader = TextLoader(file_path)
                        txt_docs = loader.load()
                        # Add metadata
                        for doc in txt_docs:
                            doc.metadata.update({
                                'source': file_path,
                                'file_name': os.path.basename(file_path),
                                'file_type': 'txt',
                                'title': os.path.basename(file_path),
                                'doc_id': self._generate_doc_id(file_path)
                            })
                        documents.extend(txt_docs)
                    elif file_ext == '.docx':
                        loader = Docx2txtLoader(file_path)
                        docx_docs = loader.load()
                        # Add metadata
                        for doc in docx_docs:
                            doc.metadata.update({
                                'source': file_path,
                                'file_name': os.path.basename(file_path),
                                'file_type': 'docx',
                                'title': os.path.basename(file_path),
                                'doc_id': self._generate_doc_id(file_path)
                            })
                        documents.extend(docx_docs)
                    elif file_ext == '.csv':
                        loader = CSVLoader(file_path)
                        csv_docs = loader.load()
                        # Add metadata
                        for doc in csv_docs:
                            doc.metadata.update({
                                'source': file_path,
                                'file_name': os.path.basename(file_path),
                                'file_type': 'csv',
                                'title': os.path.basename(file_path),
                                'doc_id': self._generate_doc_id(file_path)
                            })
                        documents.extend(csv_docs)
                except Exception as e:
                    logger.error(f"Error loading {file_path}: {str(e)}")
        
        logger.info(f"Loaded {len(documents)} documents for course {self.course_id}")
        return documents

    def _generate_doc_id(self, file_path: str) -> str:
        """Generate a unique ID for a document based on its path"""
        return hashlib.md5(file_path.encode()).hexdigest()

    def _load_pdf_with_metadata(self, file_path: str) -> List[Document]:
        """Load PDF with enhanced metadata including page numbers and titles"""
        documents = []
        try:
            # Use PyMuPDF to extract titles and metadata
            pdf = fitz.open(file_path)
            
            # Get document title from metadata or filename
            doc_title = pdf.metadata.get('title', os.path.basename(file_path))
            
            for page_num in range(len(pdf)):
                page = pdf[page_num]
                text = page.get_text()
                
                # Try to extract page/section title from the first line
                lines = text.strip().split('\n')
                page_title = lines[0].strip() if lines else f"Page {page_num + 1}"
                
                if text.strip():  # Only add non-empty pages
                    doc = Document(
                        page_content=text,
                        metadata={
                            'source': file_path,
                            'file_name': os.path.basename(file_path),
                            'file_type': 'pdf',
                            'page': page_num + 1,
                            'total_pages': len(pdf),
                            'title': doc_title,
                            'page_title': page_title,
                            'doc_id': self._generate_doc_id(file_path)
                        }
                    )
                    documents.append(doc)
            
            pdf.close()
        except Exception as e:
            logger.error(f"Error processing PDF {file_path}: {str(e)}")
        
        return documents

    def _load_pptx_with_metadata(self, file_path: str) -> List[Document]:
        """Load PowerPoint with enhanced metadata including slide numbers and titles"""
        documents = []
        try:
            prs = Presentation(file_path)
            
            for slide_num, slide in enumerate(prs.slides):
                # Extract text from slide
                text = ""
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        text += shape.text + "\n"
                
                # Try to extract slide title
                slide_title = ""
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.is_title:
                        slide_title = shape.text
                        break
                
                if not slide_title and text.strip():
                    # Use first line as title if no title shape found
                    lines = text.strip().split('\n')
                    slide_title = lines[0] if lines else f"Slide {slide_num + 1}"
                
                if text.strip():  # Only add non-empty slides
                    doc = Document(
                        page_content=text,
                        metadata={
                            'source': file_path,
                            'file_name': os.path.basename(file_path),
                            'file_type': 'pptx',
                            'slide': slide_num + 1,
                            'total_slides': len(prs.slides),
                            'title': os.path.basename(file_path),
                            'slide_title': slide_title,
                            'doc_id': self._generate_doc_id(file_path)
                        }
                    )
                    documents.append(doc)
        except Exception as e:
            logger.error(f"Error processing PowerPoint {file_path}: {str(e)}")
        
        return documents

    def _split_documents(self, documents):
        """Split documents into smaller chunks"""
        logger.info(f"Splitting {len(documents)} documents for course {self.course_id}")
        
        # Create a text splitter with appropriate chunk sizes
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", " ", ""],
            keep_separator=False
        )
        
        # Split the documents while preserving metadata
        chunks = text_splitter.split_documents(documents)
        
        # Ensure each chunk has the document metadata
        for i, chunk in enumerate(chunks):
            # Add a chunk ID to help with referencing
            chunk.metadata['chunk_id'] = f"{chunk.metadata.get('doc_id', 'unknown')}_{i}"
        
        logger.info(f"Created {len(chunks)} chunks for course {self.course_id}")
        return chunks
    
    def _initialize_vectorstore(self):
        """Initialize the vector store for the course
        
        This either loads an existing vector store or creates a new one
        from course materials if it doesn't exist.
        """
        # Create vectorstore directory if it doesn't exist
        os.makedirs(self.vectorstore_dir, exist_ok=True)
        
        # Try to load existing vectorstore
        if os.path.exists(self.vectorstore_path):
            logger.info(f"Loading existing vector store for {self.course_id}")
            try:
                with open(self.vectorstore_path, "rb") as f:
                    vectorstore = pickle.load(f)
                # Update embeddings if needed
                vectorstore._embedding = self.embeddings
                return vectorstore
            except Exception as e:
                logger.error(f"Error loading vector store: {str(e)}")
        
        # Create new vectorstore from documents
        logger.info(f"Creating new vector store for {self.course_id}")
        documents = self._load_documents()
        
        if not documents:
            logger.warning("No documents found, creating empty vector store")
            return FAISS.from_documents([], self.embeddings)
        
        chunks = self._split_documents(documents)
        vectorstore = FAISS.from_documents(chunks, self.embeddings)
        
        # Save vectorstore
        logger.info(f"Saving vector store to {self.vectorstore_path}")
        with open(self.vectorstore_path, "wb") as f:
            pickle.dump(vectorstore, f)
        
        return vectorstore
    
    def update_materials(self):
        """Update the vector store with new or modified course materials"""
        logger.info(f"Updating materials for {self.course_id}")
        
        documents = self._load_documents()
        
        if not documents:
            logger.warning("No documents found to update")
            return
        
        chunks = self._split_documents(documents)
        self.vectorstore = FAISS.from_documents(chunks, self.embeddings)
        
        # Save updated vectorstore
        logger.info(f"Saving updated vector store to {self.vectorstore_path}")
        with open(self.vectorstore_path, "wb") as f:
            pickle.dump(self.vectorstore, f)
        
        logger.info("Materials updated successfully")
    
    def _retrieve_context(self, query, top_k=5):
        """Retrieve relevant document chunks for a query"""
        if not hasattr(self, 'vectorstore') or self.vectorstore is None:
            self._initialize_vectorstore()
            
        # Get relevant documents
        docs_with_scores = self.vectorstore.similarity_search_with_score(query, k=top_k)
        
        # Format as context and keep track of references
        context_docs = []
        references = []
        
        for i, (doc, score) in enumerate(docs_with_scores):
            # Create a reference ID
            ref_id = f"ref{i+1}"
            
            # Make sure doc_id exists and is valid
            doc_id = doc.metadata.get('doc_id')
            if not doc_id or doc_id == 'unknown':
                # Generate a doc_id if not present
                if 'source' in doc.metadata:
                    doc_id = self._generate_doc_id(doc.metadata['source'])
                else:
                    # Skip documents with no valid identifiers
                    continue
            
            # Add reference to the document
            ref_info = {
                'id': ref_id,
                'doc_id': doc_id,
                'chunk_id': doc.metadata.get('chunk_id', f"{doc_id}_{i}"),
                'source': doc.metadata.get('source', ''),
                'score': score
            }
            
            # Add page or slide information if available
            if 'page' in doc.metadata:
                ref_info['page'] = doc.metadata['page']
            elif 'slide' in doc.metadata:
                ref_info['slide'] = doc.metadata['slide']
                
            # Add title information
            if 'title' in doc.metadata:
                ref_info['title'] = doc.metadata['title']
            if 'page_title' in doc.metadata:
                ref_info['page_title'] = doc.metadata['page_title']
            elif 'slide_title' in doc.metadata:
                ref_info['slide_title'] = doc.metadata['slide_title']
                
            references.append(ref_info)
            
            # Format document with reference
            context_text = f"{doc.page_content} [Source: {ref_id}]"
            context_docs.append(context_text)
        
        return "\n\n".join(context_docs), references
    
    def get_context(self, query, user_id="anonymous", top_k=5):
        """Retrieve context for a query without generating an answer
        
        Args:
            query: The search query
            user_id: Identifier for the user
            top_k: Number of top documents to retrieve
            
        Returns:
            Tuple of (context_text, references)
        """
        logger.info(f"Getting context for query in course {self.course_id}: {query}")
        
        try:
            # Get conversation history
            history = self.conversation_manager.get_conversation_history(self.course_id, user_id)
            
            # Retrieve context documents
            context, references = self._retrieve_context(query, top_k)
            
            return context, references
        except Exception as e:
            logger.error(f"Error getting context: {str(e)}")
            return "", []
    
    def _build_rag_chain(self):
        """Build the RAG chain for answering questions"""
        
        # Create a proper prompt template
        prompt_template = ChatPromptTemplate.from_template("""
        You are an AI teaching assistant for the course {course_id}.
        
        Use the following context from course materials to answer the student's question:
        
        {context}
        
        Previous conversation history:
        {conversation_history}
        
        Student question: {query}
        
        Provide a clear, accurate, and helpful response. If the context doesn't contain the answer, 
        say so honestly and suggest where the student might find more information.
        For any information you cite from the course materials, include a reference like [ref1], [ref2], etc.
        """)
        
        # Create a function to retrieve and format the context
        def retrieve_and_format_context(inputs):
            query = inputs["query"]
            context_text, references = self._retrieve_context(query)
            return {
                "context": context_text,
                "references": references,
                "query": query,
                "course_id": inputs.get("course_id", self.course_id),
                "conversation_history": inputs.get("conversation_history", "No prior conversation.")
            }
        
        # Define a chain for generating the answer
        answer_chain = prompt_template | self.llm | StrOutputParser()
        
        # Build the RAG chain
        rag_chain = (
            RunnablePassthrough.assign(
                formatted_inputs=retrieve_and_format_context
            )
            | {
                "answer": lambda x: answer_chain.invoke({
                    "context": x["formatted_inputs"]["context"],
                    "query": x["formatted_inputs"]["query"],
                    "course_id": x["formatted_inputs"]["course_id"],
                    "conversation_history": x["formatted_inputs"]["conversation_history"]
                }),
                "references": lambda x: x["formatted_inputs"]["references"]
            }
        )
        
        return rag_chain
    
    def answer_question(self, question, user_id="anonymous"):
        """Answer a question using the RAG system
        
        Args:
            question: The question to answer
            user_id: Identifier for the user asking the question
            
        Returns:
            Tuple of (answer, references) where references is a list of source documents
        """
        if not hasattr(self, 'rag_chain') or self.rag_chain is None:
            self._build_rag_chain()
            
        logger.info(f"Answering question for course {self.course_id}: {question}")
            
        # Get conversation history
        history = self.conversation_manager.get_conversation_history(self.course_id, user_id)
        
        # Run the chain
        try:
            result = self.rag_chain.invoke({
                "query": question,
                "conversation_history": history if history else "No prior conversation.",
                "course_id": self.course_id
            })
            
            # Extract answer and references directly from the result
            answer = result["answer"]
            references = result["references"]
            
            # Add user question to history, then add the response
            self.conversation_manager.add_message(
                course_id=self.course_id,
                user_id=user_id,
                role="user",
                content=question
            )

            # Add AI response to history
            self.conversation_manager.add_message(
                course_id=self.course_id,
                user_id=user_id,
                role="assistant",
                content=answer
            )
            
            return answer, references
            
        except Exception as e:
            logger.error(f"Error answering question: {str(e)}")
            return "I'm sorry, I encountered an error while processing your question. Please try again.", []
    
    def add_feedback(self, user_id, question, answer, rating, comment=None):
        """Add feedback for a question-answer pair
        
        Args:
            user_id: Student identifier
            question: The student's question
            answer: The assistant's answer
            rating: Numeric rating (1-5)
            comment: Optional text comment
            
        Returns:
            The recorded feedback entry
        """
        return self.feedback_system.add_feedback(
            course_id=self.course_id,
            user_id=user_id,
            question=question,
            answer=answer,
            rating=rating,
            comment=comment
        )
    
    def generate_feedback_report(self):
        """Generate a report on feedback for this course
        
        Returns:
            Report data dictionary
        """
        return self.feedback_system.generate_course_report(self.course_id)
    
    def export_feedback(self):
        """Export feedback data to CSV
        
        Returns:
            Path to the exported CSV file
        """
        return self.feedback_system.export_feedback_to_csv(self.course_id)
    
    def clear_conversation_history(self, user_id):
        """Clear conversation history for a user
        
        Args:
            user_id: Student identifier
            
        Returns:
            True if successful, False otherwise
        """
        return self.conversation_manager.clear_history(self.course_id, user_id)

    def get_document_by_id(self, doc_id: str, page_or_slide: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Retrieve a document by its ID and optional page/slide number
        
        Args:
            doc_id: The document ID to retrieve
            page_or_slide: The specific page or slide number (optional)
            
        Returns:
            Dictionary with document information or None if not found
        """
        # Ensure vector store is initialized
        if not hasattr(self, 'vectorstore') or self.vectorstore is None:
            self._initialize_vectorstore()
        
        # Get all documents matching the doc_id
        matching_docs = []
        
        # This is a simplified approach; in a production system, you might want 
        # to implement a separate database for more efficient document retrieval
        
        # We need to reload the documents since we don't have direct access to the chunks in the vectorstore
        documents = self._load_documents()
        
        for doc in documents:
            if doc.metadata.get('doc_id') == doc_id:
                if page_or_slide is None or doc.metadata.get('page') == page_or_slide or doc.metadata.get('slide') == page_or_slide:
                    matching_docs.append(doc)
        
        if not matching_docs:
            return None
        
        # Get the first matching document to extract metadata
        doc = matching_docs[0]
        file_path = doc.metadata.get('source')
        file_type = doc.metadata.get('file_type')
        
        # Prepare result
        result = {
            'doc_id': doc_id,
            'file_path': file_path,
            'file_name': os.path.basename(file_path) if file_path else "Unknown",
            'file_type': file_type,
            'title': doc.metadata.get('title', "Untitled Document"),
        }
        
        # Add page/slide specific information
        if file_type == 'pdf':
            result['total_pages'] = doc.metadata.get('total_pages', 0)
            if page_or_slide:
                result['page'] = page_or_slide
        elif file_type == 'pptx':
            result['total_slides'] = doc.metadata.get('total_slides', 0)
            if page_or_slide:
                result['slide'] = page_or_slide
        
        return result


# Example usage
if __name__ == "__main__":
    # Example for testing
    course_id = "DEMO101"
    rag = CourseRAG(course_id)
    
    # Test with a sample question
    question = "What are the key topics covered in this course?"
    print(f"\nQuestion: {question}")
    print(f"\nAnswer: {rag.answer_question(question)}") 