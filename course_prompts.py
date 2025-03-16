import os
import yaml
from typing import Dict, Any, Optional

class CoursePromptManager:
    """Manages course-specific prompt templates"""
    
    DEFAULT_TEMPLATE = """
    You are an AI Teaching Assistant for {course_id}.
    
    Use the following course-specific context to answer the student question.
    If you don't know the answer based on the context, be honest and say you don't know,
    but try to provide general guidance based on your knowledge.
    
    Course Context:
    {context}
    
    {conversation_history}
    
    Student Question: {question}
    
    Your response should be informative, accurate, and educational.
    If the student is asking for help on an assignment, guide them through the reasoning
    process without directly solving the problem for them.
    """
    
    # Default discipline-specific guidelines
    DISCIPLINE_GUIDELINES = {
        "math": """
        For mathematics courses:
        - Show step-by-step problem-solving approaches
        - Explain mathematical concepts with clear notation
        - Use concrete examples to illustrate abstract concepts
        - Encourage students to verify answers and check their work
        - Provide practice problems that are similar but not identical
        """,
        
        "programming": """
        For programming courses:
        - Explain code with comments on the logic, not just syntax
        - Focus on teaching design patterns and best practices
        - Don't just give code solutions - explain the thinking process
        - Encourage debugging strategies and testing approaches
        - Relate concepts to real-world software engineering scenarios
        """,
        
        "engineering": """
        For engineering courses:
        - Connect theoretical concepts to practical applications
        - Encourage system-level thinking and analysis
        - Provide diagrams and visual explanations when helpful
        - Emphasize safety considerations and ethical implications
        - Help students understand both mathematical models and physical intuition
        """,
        
        "humanities": """
        For humanities courses:
        - Help students develop critical thinking and analytical skills
        - Encourage examination of multiple perspectives on issues
        - Assist with structuring arguments and supporting claims with evidence
        - Guide students in analyzing texts and extracting key themes
        - Focus on helping students develop their own interpretations
        """
    }
    
    def __init__(self, prompts_dir: str = "course_prompts"):
        """Initialize the prompt manager
        
        Args:
            prompts_dir: Directory to store prompt templates
        """
        self.prompts_dir = prompts_dir
        os.makedirs(prompts_dir, exist_ok=True)
        
        # Create default prompts if they don't exist
        self._create_default_prompts()
    
    def _create_default_prompts(self) -> None:
        """Create default prompt templates for disciplines"""
        for discipline, guidelines in self.DISCIPLINE_GUIDELINES.items():
            file_path = os.path.join(self.prompts_dir, f"{discipline}_template.yaml")
            
            if not os.path.exists(file_path):
                template = {
                    "system_prompt": self.DEFAULT_TEMPLATE.strip(),
                    "guidelines": guidelines.strip(),
                    "examples": [
                        {
                            "question": "Can you help me understand this concept?",
                            "answer": "I'd be happy to explain this concept. Let's break it down step by step..."
                        }
                    ]
                }
                
                with open(file_path, 'w') as f:
                    yaml.dump(template, f, default_flow_style=False)
    
    def get_prompt_template(self, course_id: str, discipline: Optional[str] = None) -> Dict[str, Any]:
        """Get prompt template for a specific course
        
        Args:
            course_id: Course identifier
            discipline: Optional discipline override (math, programming, etc.)
            
        Returns:
            Dictionary with prompt template components
        """
        # First try course-specific template
        course_file = os.path.join(self.prompts_dir, f"{course_id}_template.yaml")
        
        if os.path.exists(course_file):
            with open(course_file, 'r') as f:
                return yaml.safe_load(f)
        
        # Fall back to discipline template if specified
        if discipline:
            discipline_file = os.path.join(self.prompts_dir, f"{discipline}_template.yaml")
            if os.path.exists(discipline_file):
                with open(discipline_file, 'r') as f:
                    return yaml.safe_load(f)
        
        # Use programming as default discipline if course ID suggests CS/programming
        if any(prefix in course_id.upper() for prefix in ["CS", "15-", "17-", "18-"]):
            discipline_file = os.path.join(self.prompts_dir, "programming_template.yaml")
            if os.path.exists(discipline_file):
                with open(discipline_file, 'r') as f:
                    return yaml.safe_load(f)
        
        # Return default template as fallback
        return {
            "system_prompt": self.DEFAULT_TEMPLATE.strip(),
            "guidelines": "",
            "examples": []
        }
    
    def save_prompt_template(self, course_id: str, template: Dict[str, Any]) -> None:
        """Save a course-specific prompt template
        
        Args:
            course_id: Course identifier
            template: Prompt template dictionary
        """
        file_path = os.path.join(self.prompts_dir, f"{course_id}_template.yaml")
        
        with open(file_path, 'w') as f:
            yaml.dump(template, f, default_flow_style=False)
    
    def format_prompt(self, course_id: str, context: str, question: str, 
                     conversation_history: str = "", discipline: Optional[str] = None) -> str:
        """Format a complete prompt using the template
        
        Args:
            course_id: Course identifier
            context: Retrieved context from course materials
            question: Student question
            conversation_history: Optional formatted conversation history
            discipline: Optional discipline override
            
        Returns:
            Formatted prompt string
        """
        template = self.get_prompt_template(course_id, discipline)
        
        # Combine template components
        system_prompt = template["system_prompt"]
        guidelines = template.get("guidelines", "")
        
        # Format the prompt with all variables
        formatted_prompt = system_prompt.format(
            course_id=course_id,
            context=context,
            question=question,
            conversation_history=conversation_history
        )
        
        # Add guidelines if available
        if guidelines:
            formatted_prompt += f"\n\nGuidelines for this course type:\n{guidelines}"
        
        return formatted_prompt 