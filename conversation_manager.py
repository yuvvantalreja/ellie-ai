import os
import json
import time
from typing import Dict, List, Optional, Any

class ConversationManager:
    """Manages conversation history for students across courses"""
    
    def __init__(self, storage_dir: str = "conversation_history"):
        """Initialize the conversation manager
        
        Args:
            storage_dir: Directory to store conversation history
        """
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
    
    def _get_course_dir(self, course_id: str) -> str:
        """Get the directory for a specific course's conversations"""
        course_dir = os.path.join(self.storage_dir, course_id)
        os.makedirs(course_dir, exist_ok=True)
        return course_dir
    
    def _get_user_file(self, course_id: str, user_id: str) -> str:
        """Get the file path for a specific user's conversation history"""
        course_dir = self._get_course_dir(course_id)
        return os.path.join(course_dir, f"{user_id}.json")
    
    def get_conversation_history(self, course_id: str, user_id: str, 
                                max_messages: int = 10) -> List[Dict[str, Any]]:
        """Get conversation history for a specific user in a course
        
        Args:
            course_id: Course identifier
            user_id: User identifier
            max_messages: Maximum number of recent messages to retrieve
            
        Returns:
            List of message dictionaries with 'role', 'content', and 'timestamp'
        """
        file_path = self._get_user_file(course_id, user_id)
        
        if not os.path.exists(file_path):
            return []
        
        try:
            with open(file_path, 'r') as f:
                history = json.load(f)
                return history[-max_messages:] if max_messages > 0 else history
        except Exception as e:
            print(f"Error reading conversation history: {str(e)}")
            return []
    
    def add_message(self, course_id: str, user_id: str, role: str, 
                   content: str) -> None:
        """Add a message to the conversation history
        
        Args:
            course_id: Course identifier
            user_id: User identifier
            role: Message role ('user' or 'assistant')
            content: Message content
        """
        file_path = self._get_user_file(course_id, user_id)
        
        # Create new history or load existing
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    history = json.load(f)
            except Exception:
                history = []
        else:
            history = []
        
        # Add new message
        message = {
            "role": role,
            "content": content,
            "timestamp": time.time()
        }
        history.append(message)
        
        # Save updated history
        with open(file_path, 'w') as f:
            json.dump(history, f, indent=2)
    
    def get_formatted_history(self, course_id: str, user_id: str, 
                             max_messages: int = 5) -> str:
        """Get formatted conversation history for context window
        
        Args:
            course_id: Course identifier
            user_id: User identifier
            max_messages: Maximum number of recent messages to include
            
        Returns:
            Formatted string of conversation history
        """
        history = self.get_conversation_history(course_id, user_id, max_messages)
        
        if not history:
            return ""
        
        formatted_history = "Previous conversation:\n\n"
        for msg in history:
            role_name = "Student" if msg["role"] == "user" else "Assistant"
            formatted_history += f"{role_name}: {msg['content']}\n\n"
        
        return formatted_history
    
    def clear_history(self, course_id: str, user_id: str) -> bool:
        """Clear conversation history for a user
        
        Args:
            course_id: Course identifier
            user_id: User identifier
            
        Returns:
            True if history was cleared, False otherwise
        """
        file_path = self._get_user_file(course_id, user_id)
        
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                return True
            except Exception as e:
                print(f"Error clearing conversation history: {str(e)}")
        
        return False 