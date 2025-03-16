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
from course_rag import CourseRAG
from course_prompts import CoursePromptManager
from conversation_manager import ConversationManager
from feedback_system import FeedbackSystem
from dotenv import load_dotenv

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
os.makedirs(MATERIALS_DIR, exist_ok=True)
os.makedirs("templates", exist_ok=True)
os.makedirs("static", exist_ok=True)
os.makedirs("static/css", exist_ok=True)
os.makedirs("static/js", exist_ok=True)
os.makedirs("static/images", exist_ok=True)


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


if __name__ == '__main__':
    # Create HTML templates and static files
    print("Creating templates directory and HTML files...")
    app.run(debug=True, port=5000) 