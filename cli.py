#!/usr/bin/env python3
import os
import argparse
import time
from course_rag import CourseRAG
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_course_materials_directory(course_id):
    """Set up course materials directory structure"""
    materials_dir = os.getenv("MATERIALS_DIR", "course_materials")
    course_dir = os.path.join(materials_dir, course_id)
    
    if not os.path.exists(course_dir):
        os.makedirs(course_dir, exist_ok=True)
        print(f"Created course directory: {course_dir}")
        print(f"Please add your course materials (PDF, DOCX, TXT, etc.) to this directory")
        return False
    
    files = os.listdir(course_dir)
    if not any(os.path.isfile(os.path.join(course_dir, f)) for f in files):
        print(f"No files found in {course_dir}")
        print(f"Please add your course materials (PDF, DOCX, TXT, etc.) to this directory")
        return False
    
    return True


def interactive_mode(course_id):
    """Run the RAG system in interactive mode"""
    # Check if course materials directory exists and has files
    if not setup_course_materials_directory(course_id):
        proceed = input("Continue without materials? (y/n): ").lower()
        if proceed != 'y':
            return
    
    print(f"\nInitializing AI Teaching Assistant for {course_id}...")
    print("This may take a moment while we process your course materials...\n")
    
    # Initialize RAG system
    rag = CourseRAG(course_id)
    
    print(f"\nAI Teaching Assistant for {course_id} is ready!")
    print("Type 'exit' or 'quit' to end the session")
    print("Type 'update' to refresh the course materials\n")
    
    while True:
        question = input("\nStudent Question: ")
        
        if question.lower() in ['exit', 'quit']:
            print("Ending session. Goodbye!")
            break
        
        if question.lower() == 'update':
            print("Updating course materials...")
            rag.update_materials()
            print("Course materials updated!")
            continue
        
        if not question.strip():
            continue
        
        print("\nThinking...")
        start_time = time.time()
        
        response = rag.answer_question(question)
        
        elapsed_time = time.time() - start_time
        print(f"\nAI Teaching Assistant ({elapsed_time:.2f}s):")
        print(response)


def main():
    parser = argparse.ArgumentParser(description="Course-specific AI Teaching Assistant")
    parser.add_argument("--course", "-c", required=True, help="Course ID (e.g., CS101)")
    
    args = parser.parse_args()
    
    # Run in interactive mode
    interactive_mode(args.course)


if __name__ == "__main__":
    main() 