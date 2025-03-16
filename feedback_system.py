import os
import json
import csv
import time
import datetime
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter

class FeedbackSystem:
    """System for collecting and analyzing student feedback"""
    
    def __init__(self, feedback_dir: str = "feedback_data"):
        """Initialize the feedback system
        
        Args:
            feedback_dir: Directory to store feedback data
        """
        self.feedback_dir = feedback_dir
        os.makedirs(feedback_dir, exist_ok=True)
        
        # Create subdirectories for different data types
        self.ratings_dir = os.path.join(feedback_dir, "ratings")
        self.reports_dir = os.path.join(feedback_dir, "reports")
        os.makedirs(self.ratings_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)
    
    def _get_course_feedback_file(self, course_id: str) -> str:
        """Get the file path for a specific course's feedback data"""
        return os.path.join(self.ratings_dir, f"{course_id}_feedback.json")
    
    def add_feedback(self, course_id: str, user_id: str, 
                   question: str, answer: str, rating: int, 
                   comment: Optional[str] = None) -> Dict[str, Any]:
        """Record student feedback for an answer
        
        Args:
            course_id: Course identifier
            user_id: User identifier
            question: The student's question
            answer: The assistant's answer
            rating: Numeric rating (1-5)
            comment: Optional text comment on the answer
            
        Returns:
            The recorded feedback entry
        """
        file_path = self._get_course_feedback_file(course_id)
        
        # Create new feedback list or load existing
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    feedback_list = json.load(f)
            except Exception:
                feedback_list = []
        else:
            feedback_list = []
        
        # Create feedback entry
        feedback_entry = {
            "id": len(feedback_list) + 1,
            "user_id": user_id,
            "question": question,
            "answer": answer,
            "rating": rating,
            "comment": comment,
            "timestamp": time.time(),
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Add to feedback list
        feedback_list.append(feedback_entry)
        
        # Save updated feedback
        with open(file_path, 'w') as f:
            json.dump(feedback_list, f, indent=2)
        
        return feedback_entry
    
    def get_course_feedback(self, course_id: str) -> List[Dict[str, Any]]:
        """Get all feedback for a specific course
        
        Args:
            course_id: Course identifier
            
        Returns:
            List of feedback entries
        """
        file_path = self._get_course_feedback_file(course_id)
        
        if not os.path.exists(file_path):
            return []
        
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading feedback data: {str(e)}")
            return []
    
    def generate_course_report(self, course_id: str) -> Dict[str, Any]:
        """Generate a comprehensive report for a course
        
        Args:
            course_id: Course identifier
            
        Returns:
            Report data dictionary
        """
        feedback_list = self.get_course_feedback(course_id)
        
        if not feedback_list:
            return {
                "course_id": course_id,
                "date": datetime.datetime.now().strftime("%Y-%m-%d"),
                "total_feedback": 0,
                "error": "No feedback data available"
            }
        
        # Calculate statistics
        ratings = [entry["rating"] for entry in feedback_list]
        avg_rating = sum(ratings) / len(ratings)
        rating_counts = Counter(ratings)
        
        # Extract common themes from comments (simple approach)
        comments = [entry["comment"] for entry in feedback_list if entry.get("comment")]
        
        # Create report
        report = {
            "course_id": course_id,
            "date_generated": datetime.datetime.now().strftime("%Y-%m-%d"),
            "total_feedback": len(feedback_list),
            "average_rating": round(avg_rating, 2),
            "rating_distribution": {str(k): v for k, v in rating_counts.items()},
            "sample_comments": comments[:5] if comments else [],
            "first_date": feedback_list[0]["date"],
            "last_date": feedback_list[-1]["date"]
        }
        
        # Save report
        report_file = os.path.join(
            self.reports_dir, 
            f"{course_id}_report_{datetime.datetime.now().strftime('%Y%m%d')}.json"
        )
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Generate visualizations
        self._generate_report_visualizations(course_id, feedback_list, report)
        
        return report
    
    def _generate_report_visualizations(self, course_id: str, 
                                      feedback_list: List[Dict[str, Any]], 
                                      report: Dict[str, Any]) -> Tuple[str, str]:
        """Generate visualizations for the report
        
        Args:
            course_id: Course identifier
            feedback_list: List of feedback entries
            report: Report data dictionary
            
        Returns:
            Tuple of file paths for the generated charts
        """
        # Convert to DataFrame for easier analysis
        df = pd.DataFrame(feedback_list)
        
        # Create a ratings distribution chart
        plt.figure(figsize=(10, 6))
        rating_counts = df['rating'].value_counts().sort_index()
        bars = plt.bar(rating_counts.index, rating_counts.values, color='skyblue')
        plt.title(f'Rating Distribution for {course_id}')
        plt.xlabel('Rating')
        plt.ylabel('Count')
        plt.xticks(range(1, 6))
        
        # Add count labels on bars
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{height}', ha='center', va='bottom')
        
        # Save the chart
        ratings_chart_path = os.path.join(
            self.reports_dir,
            f"{course_id}_ratings_{datetime.datetime.now().strftime('%Y%m%d')}.png"
        )
        plt.savefig(ratings_chart_path)
        plt.close()
        
        # Create a trend chart if we have timestamps
        if 'timestamp' in df.columns and len(df) > 1:
            plt.figure(figsize=(12, 6))
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            
            # Group by date and calculate average rating
            daily_ratings = df.groupby(df['date'].dt.date)['rating'].mean()
            
            plt.plot(daily_ratings.index, daily_ratings.values, marker='o', linestyle='-')
            plt.title(f'Rating Trend Over Time for {course_id}')
            plt.xlabel('Date')
            plt.ylabel('Average Rating')
            plt.ylim(0.5, 5.5)
            plt.grid(True, linestyle='--', alpha=0.7)
            
            # Save the chart
            trend_chart_path = os.path.join(
                self.reports_dir,
                f"{course_id}_trend_{datetime.datetime.now().strftime('%Y%m%d')}.png"
            )
            plt.savefig(trend_chart_path)
            plt.close()
            
            return ratings_chart_path, trend_chart_path
        
        return ratings_chart_path, ""
    
    def export_feedback_to_csv(self, course_id: str) -> str:
        """Export course feedback to CSV format
        
        Args:
            course_id: Course identifier
            
        Returns:
            Path to the exported CSV file
        """
        feedback_list = self.get_course_feedback(course_id)
        
        if not feedback_list:
            return ""
        
        # Prepare export file
        csv_file = os.path.join(
            self.reports_dir, 
            f"{course_id}_feedback_{datetime.datetime.now().strftime('%Y%m%d')}.csv"
        )
        
        # Write to CSV
        with open(csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(
                f, 
                fieldnames=["id", "date", "user_id", "question", "rating", "comment"]
            )
            writer.writeheader()
            
            for entry in feedback_list:
                # Extract only the fields we want to export
                row = {
                    "id": entry["id"],
                    "date": entry["date"],
                    "user_id": entry["user_id"],
                    "question": entry["question"],
                    "rating": entry["rating"],
                    "comment": entry.get("comment", "")
                }
                writer.writerow(row)
        
        return csv_file 