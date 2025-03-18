from flask import Flask, render_template, request, jsonify, send_file, session, Response
import os
import threading
import time
import datetime
import uuid
import json
import io
import fitz  # PyMuPDF
from pptx import Presentation
from PIL import Image
import base64
import requests
import numpy as np
from course_rag import CourseRAG
from course_prompts import CoursePromptManager
from conversation_manager import ConversationManager
from feedback_system import FeedbackSystem
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "ellie-cmu-ai-assistant-secret-key")

# Add template filters
@app.template_filter('now')
def filter_now(format_='%Y'):
    """Return the current year or formatted date"""
    return datetime.datetime.now().strftime(format_)

# Global dict to store RAG instances for different courses
rag_instances = {}
rag_locks = {}  # Locks to prevent concurrent access to RAG instances

# Initialize shared components
prompt_manager = CoursePromptManager()
conversation_manager = ConversationManager()
feedback_system = FeedbackSystem()

# Directory setup
MATERIALS_DIR = os.getenv("MATERIALS_DIR", "course_materials")
UPLOAD_FOLDER = os.path.join("static", "uploads")
os.makedirs(MATERIALS_DIR, exist_ok=True)
os.makedirs("templates", exist_ok=True)
os.makedirs("static", exist_ok=True)
os.makedirs("static/css", exist_ok=True)
os.makedirs("static/js", exist_ok=True)
os.makedirs("static/images", exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Configure app
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# Get API keys from environment variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama3-70b-8192")
GROQ_VISION_MODEL = os.getenv("GROQ_VISION_MODEL", "llama-3.2-90b-vision-preview")

def get_rag_instance(course_id, discipline=None):
    """Get or create a RAG instance for the given course"""
    if course_id not in rag_locks:
        rag_locks[course_id] = threading.Lock()
    
    with rag_locks[course_id]:
        if course_id not in rag_instances:
            rag_instances[course_id] = CourseRAG(course_id, discipline=discipline)
        
        return rag_instances[course_id]


def get_user_id():
    """Get or create a unique user ID for the session"""
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    return session['user_id']


@app.route('/')
def index():
    """Render the main page"""
    courses = []
    
    # Get list of course directories
    if os.path.exists(MATERIALS_DIR):
        courses = [d for d in os.listdir(MATERIALS_DIR) 
                 if os.path.isdir(os.path.join(MATERIALS_DIR, d))]
    
    return render_template('index.html', courses=courses)


@app.route('/course/<course_id>')
def course_page(course_id):
    """Render the course-specific chat page"""
    # Ensure user ID is set
    user_id = get_user_id()
    
    # Get conversation history
    history = conversation_manager.get_conversation_history(course_id, user_id)
    
    return render_template('chat.html', course_id=course_id, history=history)


@app.route('/api/courses')
def get_courses():
    """API endpoint to get available courses"""
    courses = []
    
    if os.path.exists(MATERIALS_DIR):
        courses = [d for d in os.listdir(MATERIALS_DIR) 
                 if os.path.isdir(os.path.join(MATERIALS_DIR, d))]
    
    return jsonify({'courses': courses})


# Helper function to make data JSON serializable
def make_json_serializable(obj):
    """Convert NumPy types and other non-serializable types to Python native types"""
    if isinstance(obj, np.float32) or isinstance(obj, np.float64):
        return float(obj)
    elif isinstance(obj, np.int32) or isinstance(obj, np.int64):
        return int(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_json_serializable(item) for item in obj]
    else:
        return obj


@app.route('/api/ask', methods=['POST'])
def ask_question():
    """API endpoint to answer a question"""
    data = request.json
    if not data or 'question' not in data or 'course_id' not in data:
        return jsonify({"error": "Missing required parameters"}), 400
    
    question = data['question']
    course_id = data['course_id']
    user_id = get_user_id()
    
    # Get the RAG instance
    rag = get_rag_instance(course_id, data.get('discipline'))
    
    try:
        # Get answer from RAG system
        answer, references = rag.answer_question(question, user_id)
        
        # Convert references to JSON serializable format
        references = make_json_serializable(references)
        
        # Format the references for the UI
        formatted_refs = []
        for i, ref in enumerate(references):
            # Skip references with invalid doc_id
            if not ref.get("doc_id") or ref.get("doc_id") == "unknown":
                continue
                
            ref_text = f"[ref{i+1}]"
            page_or_slide = None
            if 'page' in ref:
                page_or_slide = ref['page']
            elif 'slide' in ref:
                page_or_slide = ref['slide']
                
            formatted_refs.append({
                "id": ref_text,
                "doc_id": ref.get("doc_id", ""),
                "source": os.path.basename(ref.get("source", "")),
                "page_or_slide": page_or_slide,
                "title": ref.get("title", ""),
                "subtitle": ref.get("page_title", ref.get("slide_title", ""))
            })
        
        # Save the conversation with references
        conversation_manager.add_message(course_id, user_id, "user", question)
        conversation_manager.add_message(course_id, user_id, "assistant", answer, references=references)
        
        return jsonify({
            "answer": answer, 
            "references": formatted_refs
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/history', methods=['GET'])
def get_history():
    """API endpoint to get conversation history"""
    course_id = request.args.get('course_id')
    
    if not course_id:
        return jsonify({'error': 'Course ID is required'}), 400
    
    # Get user ID from session
    user_id = get_user_id()
    
    history = conversation_manager.get_conversation_history(course_id, user_id)
    
    return jsonify({'history': history})


@app.route('/api/history/clear', methods=['POST'])
def clear_history():
    """API endpoint to clear conversation history"""
    data = request.json
    course_id = data.get('course_id')
    
    if not course_id:
        return jsonify({'error': 'Course ID is required'}), 400
    
    # Get user ID from session
    user_id = get_user_id()
    
    success = conversation_manager.clear_history(course_id, user_id)
    
    return jsonify({'success': success})


@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    """API endpoint to submit feedback"""
    data = request.json
    course_id = data.get('course_id')
    question = data.get('question')
    answer = data.get('answer')
    rating = data.get('rating')
    comment = data.get('comment')
    
    if not all([course_id, question, answer, rating]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Validate rating
    try:
        rating = int(rating)
        if not 1 <= rating <= 5:
            raise ValueError("Rating must be between 1 and 5")
    except ValueError:
        return jsonify({'error': 'Rating must be an integer between 1 and 5'}), 400
    
    # Get user ID from session
    user_id = get_user_id()
    
    try:
        rag = get_rag_instance(course_id)
        feedback = rag.add_feedback(user_id, question, answer, rating, comment)
        
        return jsonify({'success': True, 'feedback': feedback})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/feedback/report', methods=['GET'])
def get_feedback_report():
    """API endpoint to get feedback report"""
    course_id = request.args.get('course_id')
    
    if not course_id:
        return jsonify({'error': 'Course ID is required'}), 400
    
    try:
        rag = get_rag_instance(course_id)
        report = rag.generate_feedback_report()
        
        return jsonify({'report': report})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/feedback/export', methods=['GET'])
def export_feedback():
    """API endpoint to export feedback data"""
    course_id = request.args.get('course_id')
    
    if not course_id:
        return jsonify({'error': 'Course ID is required'}), 400
    
    try:
        rag = get_rag_instance(course_id)
        csv_file = rag.export_feedback()
        
        if not csv_file or not os.path.exists(csv_file):
            return jsonify({'error': 'No feedback data available'}), 404
        
        return send_file(csv_file, as_attachment=True, download_name=f"{course_id}_feedback.csv")
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/update_materials', methods=['POST'])
def update_materials():
    """API endpoint to update course materials"""
    data = request.json
    course_id = data.get('course_id')
    
    if not course_id:
        return jsonify({'error': 'Course ID is required'}), 400
    
    try:
        rag = get_rag_instance(course_id)
        rag.update_materials()
        return jsonify({'success': True, 'message': 'Materials updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/upload_materials', methods=['POST'])
def upload_materials():
    """API endpoint to upload course materials"""
    # Check if course_id is provided
    course_id = request.form.get('course_id')
    if not course_id:
        return jsonify({'error': 'Course ID is required'}), 400
    
    # Check if course directory exists
    course_dir = os.path.join(MATERIALS_DIR, course_id)
    if not os.path.exists(course_dir):
        return jsonify({'error': f'Course {course_id} not found'}), 404
    
    # Check if files were uploaded
    if 'materials' not in request.files:
        return jsonify({'error': 'No files uploaded'}), 400
    
    files = request.files.getlist('materials')
    if not files or files[0].filename == '':
        return jsonify({'error': 'No files selected'}), 400
    
    # Define allowed file extensions
    ALLOWED_EXTENSIONS = {'pdf', 'pptx', 'docx', 'txt', 'csv'}
    
    # Process uploaded files
    uploaded_files = []
    for file in files:
        if file and '.' in file.filename:
            ext = file.filename.rsplit('.', 1)[1].lower()
            if ext in ALLOWED_EXTENSIONS:
                filename = secure_filename(file.filename)
                file_path = os.path.join(course_dir, filename)
                file.save(file_path)
                uploaded_files.append(filename)
    
    if not uploaded_files:
        return jsonify({'error': 'No valid files were uploaded'}), 400
    
    try:
        # Update materials in the RAG system
        rag = get_rag_instance(course_id)
        rag.update_materials()
        
        return jsonify({
            'success': True,
            'message': f'Successfully uploaded {len(uploaded_files)} file(s) to {course_id}',
            'files': uploaded_files
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/create_course', methods=['POST'])
def create_course():
    """API endpoint to create a new course"""
    data = request.json
    course_id = data.get('course_id')
    discipline = data.get('discipline')
    
    if not course_id:
        return jsonify({'error': 'Course ID is required'}), 400
    
    try:
        # Create course directory
        course_dir = os.path.join(MATERIALS_DIR, course_id)
        os.makedirs(course_dir, exist_ok=True)
        
        # Create course-specific prompt if discipline is provided
        if discipline:
            template = prompt_manager.get_prompt_template(discipline=discipline)
            prompt_manager.save_prompt_template(course_id, template)
        
        return jsonify({
            'success': True, 
            'message': f'Course {course_id} created successfully. Add materials to {course_dir}'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/prompts/<course_id>', methods=['GET'])
def get_course_prompt(course_id):
    """API endpoint to get course prompt template"""
    try:
        template = prompt_manager.get_prompt_template(course_id)
        return jsonify({'template': template})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/prompts/<course_id>', methods=['POST'])
def update_course_prompt(course_id):
    """API endpoint to update course prompt template"""
    data = request.json
    
    if not data:
        return jsonify({'error': 'Prompt template data is required'}), 400
    
    try:
        prompt_manager.save_prompt_template(course_id, data)
        return jsonify({'success': True, 'message': 'Prompt template updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/instructor/<course_id>')
def instructor_dashboard(course_id):
    """Render the instructor dashboard for a course"""
    try:
        rag = get_rag_instance(course_id)
        report = rag.generate_feedback_report()
        template = prompt_manager.get_prompt_template(course_id)
        
        return render_template('instructor.html', course_id=course_id, report=report, template=template)
    except Exception as e:
        return render_template('error.html', error=str(e))


@app.route('/api/document/<course_id>/<doc_id>', methods=['GET'])
def get_document(course_id, doc_id):
    """API endpoint to get document metadata"""
    page_or_slide = request.args.get('page') or request.args.get('slide')
    if page_or_slide:
        try:
            page_or_slide = int(page_or_slide)
        except ValueError:
            page_or_slide = None
    
    rag = get_rag_instance(course_id)
    doc_info = rag.get_document_by_id(doc_id, page_or_slide)
    
    if not doc_info:
        return jsonify({"error": "Document not found"}), 404
    
    return jsonify(doc_info)

@app.route('/api/document/render/<course_id>/<doc_id>', methods=['GET'])
def render_document(course_id, doc_id):
    """Render a document page or slide as an image"""
    # Get page or slide number from query parameters
    page_or_slide = request.args.get('page') or request.args.get('slide')
    if page_or_slide:
        try:
            page_or_slide = int(page_or_slide)
        except ValueError:
            return jsonify({"error": "Invalid page or slide number"}), 400
    
    # Get document info
    rag = get_rag_instance(course_id)
    doc_info = rag.get_document_by_id(doc_id, page_or_slide)
    
    if not doc_info:
        return jsonify({"error": "Document not found"}), 404
    
    file_path = doc_info.get('file_path')
    file_type = doc_info.get('file_type')
    
    if not file_path or not os.path.exists(file_path):
        return jsonify({"error": "Document file not found"}), 404
    
    try:
        # Render based on file type
        if file_type == 'pdf' and page_or_slide:
            # Render PDF page
            pdf = fitz.open(file_path)
            if page_or_slide < 1 or page_or_slide > len(pdf):
                return jsonify({"error": "Page number out of range"}), 400
                
            page = pdf[page_or_slide - 1]  # 0-indexed
            pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
            img_bytes = pix.tobytes("png")
            
            return Response(img_bytes, mimetype='image/png')
            
        elif file_type == 'pptx' and page_or_slide:
            # Render PowerPoint slide
            prs = Presentation(file_path)
            if page_or_slide < 1 or page_or_slide > len(prs.slides):
                return jsonify({"error": "Slide number out of range"}), 400
            
            # This is a simplification - actual rendering would require
            # converting the slide to an image using additional libraries
            slide = prs.slides[page_or_slide - 1]  # 0-indexed
            
            # Return slide content as JSON for now
            slide_content = []
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    slide_content.append(shape.text)
            
            return jsonify({
                "type": "text",
                "content": "\n".join(slide_content)
            })
            
        else:
            # For other file types, just return the file
            return send_file(file_path)
            
    except Exception as e:
        return jsonify({"error": f"Error rendering document: {str(e)}"}), 500

@app.route('/api/document/content/<course_id>/<doc_id>', methods=['GET'])
def get_document_content(course_id, doc_id):
    """Get the text content of a document page or slide"""
    # Get page or slide number from query parameters
    page_or_slide = request.args.get('page') or request.args.get('slide')
    if page_or_slide:
        try:
            page_or_slide = int(page_or_slide)
        except ValueError:
            return jsonify({"error": "Invalid page or slide number"}), 400
    
    # Get document info
    rag = get_rag_instance(course_id)
    doc_info = rag.get_document_by_id(doc_id, page_or_slide)
    
    if not doc_info:
        return jsonify({"error": "Document not found"}), 404
    
    file_path = doc_info.get('file_path')
    file_type = doc_info.get('file_type')
    
    if not file_path or not os.path.exists(file_path):
        return jsonify({"error": "Document file not found"}), 404
    
    try:
        # Extract content based on file type
        if file_type == 'pdf' and page_or_slide:
            # Get PDF page text
            pdf = fitz.open(file_path)
            if page_or_slide < 1 or page_or_slide > len(pdf):
                return jsonify({"error": "Page number out of range"}), 400
                
            page = pdf[page_or_slide - 1]  # 0-indexed
            text = page.get_text()
            
            return jsonify({
                "content": text,
                "title": doc_info.get('title', ''),
                "page": page_or_slide,
                "total_pages": doc_info.get('total_pages', 0)
            })
            
        elif file_type == 'pptx' and page_or_slide:
            # Get PowerPoint slide text
            prs = Presentation(file_path)
            if page_or_slide < 1 or page_or_slide > len(prs.slides):
                return jsonify({"error": "Slide number out of range"}), 400
            
            slide = prs.slides[page_or_slide - 1]  # 0-indexed
            
            # Extract slide title and content
            slide_title = ""
            slide_content = []
            
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    if shape.is_title:
                        slide_title = shape.text
                    else:
                        slide_content.append(shape.text)
            
            return jsonify({
                "content": "\n".join(slide_content),
                "title": slide_title,
                "slide": page_or_slide,
                "total_slides": doc_info.get('total_slides', 0)
            })
            
        else:
            # For other file types, return an error
            return jsonify({"error": "Content extraction not supported for this file type"}), 400
            
    except Exception as e:
        return jsonify({"error": f"Error extracting content: {str(e)}"}), 500

@app.route('/api/document/download/<course_id>/<doc_id>', methods=['GET'])
def download_document(course_id, doc_id):
    """Download a source document"""
    rag = get_rag_instance(course_id)
    doc_info = rag.get_document_by_id(doc_id)
    
    if not doc_info:
        return jsonify({"error": "Document not found"}), 404
    
    file_path = doc_info.get('file_path')
    
    if not file_path or not os.path.exists(file_path):
        return jsonify({"error": "Document file not found"}), 404
    
    try:
        return send_file(
            file_path,
            as_attachment=True,
            download_name=os.path.basename(file_path)
        )
    except Exception as e:
        return jsonify({"error": f"Error downloading document: {str(e)}"}), 500

@app.route('/api/ask_with_image', methods=['POST'])
def ask_question_with_image():
    """API endpoint to answer a question that may include an image"""
    if not request.form.get('course_id'):
        return jsonify({"error": "Missing course_id parameter"}), 400
    
    course_id = request.form.get('course_id')
    question = request.form.get('question', '')
    user_id = get_user_id()
    
    print(f"Received image upload request for course {course_id}")
    print(f"Files in request: {request.files.keys()}")
    
    # Check if an image was uploaded
    image_file = None
    image_path = None
    if 'image' in request.files and request.files['image'].filename:
        image_file = request.files['image']
        print(f"Image file detected: {image_file.filename}, {image_file.content_type}")
        if image_file and allowed_file(image_file.filename):
            filename = secure_filename(f"{user_id}_{int(time.time())}_{image_file.filename}")
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(image_path)
            print(f"Image saved to: {image_path}")
        else:
            print(f"Invalid image file or not allowed: {image_file.filename}")
    else:
        print("No image file found in request")
    
    try:
        # Get RAG instance for context
        rag = get_rag_instance(course_id)
        
        # If there's an image, use the vision model with the image
        if image_path:
            print(f"Using vision model with image: {image_path}")
            # First, get relevant context from the RAG system based on the text question
            rag_context = ""
            if question.strip():
                rag_context, _ = rag.get_context(question, user_id)
            
            # Prepare prompt with course context
            system_prompt = f"You are Ellie, an AI Teaching Assistant for course {course_id}. Answer the student's question based on the image they've shared and your knowledge of the course material."
            
            if rag_context:
                system_prompt += f"\n\nHere is relevant information from the course materials that may help you answer:\n{rag_context}"
            
            # Call the vision model with the image
            print(f"Calling vision model {GROQ_VISION_MODEL}")
            answer = call_vision_model(system_prompt, question, image_path)
            print("Vision model response received")
            
            # Save the conversation with the image path
            conversation_manager.add_message(
                course_id, 
                user_id,
                "user", 
                question if question else "[Image uploaded without text]",
                references=[{"image_path": image_path}]
            )
            conversation_manager.add_message(course_id, user_id, "assistant", answer)
            
            return jsonify({
                "answer": answer,
                "references": []  # No direct references for image-based queries yet
            })
        else:
            print("No image path, falling back to text-only response")
            # If no image, use the regular RAG-based approach
            answer, references = rag.answer_question(question, user_id)
            
            # Convert references to JSON serializable format
            references = make_json_serializable(references)
            
            # Format the references for the UI
            formatted_refs = []
            for i, ref in enumerate(references):
                # Skip references with invalid doc_id
                if not ref.get("doc_id") or ref.get("doc_id") == "unknown":
                    continue
                    
                ref_text = f"[ref{i+1}]"
                page_or_slide = None
                if 'page' in ref:
                    page_or_slide = ref['page']
                elif 'slide' in ref:
                    page_or_slide = ref['slide']
                    
                formatted_refs.append({
                    "id": ref_text,
                    "doc_id": ref.get("doc_id", ""),
                    "source": os.path.basename(ref.get("source", "")),
                    "page_or_slide": page_or_slide,
                    "title": ref.get("title", ""),
                    "subtitle": ref.get("page_title", ref.get("slide_title", ""))
                })
            
            return jsonify({
                "answer": answer,
                "references": formatted_refs
            })
            
    except Exception as e:
        print(f"Error in ask_question_with_image: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def call_vision_model(system_prompt, user_question, image_path):
    """Call the GROQ Vision model API with the image and question"""
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set in environment variables")
    
    print(f"Processing image: {image_path}")
    
    # Get image data as base64
    with open(image_path, "rb") as image_file:
        image_data = base64.b64encode(image_file.read()).decode('utf-8')
    
    print(f"Image encoded as base64 (length: {len(image_data)})")
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    # Combine system prompt with user question since system messages are incompatible with image inputs
    combined_prompt = f"{system_prompt}\n\nQuestion: {user_question if user_question else 'Can you analyze and explain this image?'}"
    
    payload = {
        "model": GROQ_VISION_MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": combined_prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
                ]
            }
        ],
        "temperature": 0.2
    }
    
    print(f"Sending request to Groq Vision API with model: {GROQ_VISION_MODEL}")
    
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        json=payload
    )
    
    if response.status_code != 200:
        error_msg = f"Error calling GROQ Vision API (status {response.status_code}): {response.text}"
        print(error_msg)
        raise Exception(error_msg)
    
    result = response.json()
    print("Vision API response received successfully")
    
    return result['choices'][0]['message']['content']

if __name__ == '__main__':
    # Create HTML templates and static files
    print("Creating templates directory and HTML files...")
    app.run(debug=True, port=5000) 