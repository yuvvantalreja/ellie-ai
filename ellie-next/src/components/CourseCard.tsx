'use client';

import React from 'react';
import { Card, Button } from 'react-bootstrap';
import Link from 'next/link';

interface CourseCardProps {
    courseId: string;
}

const CourseCard: React.FC<CourseCardProps> = ({ courseId }) => {
    return (
        <div className="col-md-4 mb-4">
            <Card className="course-card h-100">
                <Card.Body className="d-flex flex-column">
                    <Card.Title>
                        <i className="bi bi-mortarboard me-2"></i>{courseId}
                    </Card.Title>
                    <Card.Text className="flex-grow-1">
                        Get help with assignments, concepts, and course materials for {courseId}.
                    </Card.Text>
                    <Link href={`/course/${courseId}`} passHref>
                        <Button variant="primary" className="mt-3">
                            <i className="bi bi-chat-dots me-1"></i> Chat with Ellie
                        </Button>
                    </Link>
                </Card.Body>
            </Card>
        </div>
    );
};

export default CourseCard; 