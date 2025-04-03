'use client';

import React, { useState } from 'react';
import { Card, Button, Modal, Form } from 'react-bootstrap';
import axios from 'axios';

// Custom Toast component
const Toast = ({ message, type, onClose }: { message: string; type: string; onClose: () => void }) => {
    return (
        <div className={`custom-alert alert-${type}`}>
            <i className={`bi bi-${type === 'error' ? 'exclamation-triangle' : 'check-circle'}`}></i>
            {message}
        </div>
    );
};

const CreateCourseCard: React.FC = () => {
    const [showModal, setShowModal] = useState(false);
    const [courseId, setCourseId] = useState('');
    const [discipline, setDiscipline] = useState('');
    const [files, setFiles] = useState<FileList | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [toast, setToast] = useState<{ message: string; type: string } | null>(null);

    const handleClose = () => setShowModal(false);
    const handleShow = () => setShowModal(true);

    const handleSubmit = async () => {
        if (!courseId) {
            setToast({ message: 'Please enter a valid Course ID', type: 'error' });
            return;
        }

        setIsLoading(true);

        try {
            // First create the course
            const courseResponse = await axios.post('/api/create_course', {
                course_id: courseId,
                discipline: discipline || undefined,
            });

            // If there are files to upload, upload them
            if (files && files.length > 0) {
                const formData = new FormData();
                formData.append('course_id', courseId);

                // Append all files
                for (let i = 0; i < files.length; i++) {
                    formData.append('materials', files[i]);
                }

                // Upload the files
                await axios.post('/api/upload_materials', formData);
            }

            setToast({ message: 'Course created successfully!', type: 'success' });

            // Clear form and close modal
            setCourseId('');
            setDiscipline('');
            setFiles(null);
            setShowModal(false);

            // Reload page after a short delay
            setTimeout(() => {
                window.location.reload();
            }, 1500);

        } catch (error) {
            console.error('Error creating course:', error);
            setToast({
                message: `Error creating course: ${error instanceof Error ? error.message : 'Unknown error'}`,
                type: 'error'
            });
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <>
            {toast && (
                <Toast
                    message={toast.message}
                    type={toast.type}
                    onClose={() => setToast(null)}
                />
            )}

            <div className="col-md-4 mb-4">
                <Card className="course-card create-course-card h-100" onClick={handleShow}>
                    <Card.Body className="d-flex flex-column">
                        <div className="create-course-icon">
                            <i className="bi bi-plus-circle"></i>
                        </div>
                        <Card.Title>Create New Course</Card.Title>
                        <Card.Text className="flex-grow-1">
                            Set up a new course with Ellie to start getting AI assistance.
                        </Card.Text>
                        <Button variant="outline-primary" className="mt-3">
                            <i className="bi bi-plus-lg me-1"></i> Create Course
                        </Button>
                    </Card.Body>
                </Card>
            </div>

            <Modal show={showModal} onHide={handleClose} size="lg">
                <Modal.Header closeButton>
                    <Modal.Title>
                        <i className="bi bi-plus-circle me-2"></i>Create New Course
                    </Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <Form>
                        <Form.Group className="mb-3">
                            <Form.Label>Course ID (e.g., 15-122, 18-100)</Form.Label>
                            <Form.Control
                                type="text"
                                placeholder="Enter CMU course ID"
                                value={courseId}
                                onChange={(e) => setCourseId(e.target.value)}
                                required
                            />
                            <Form.Text className="text-muted">
                                This will create a folder where you can add course materials.
                            </Form.Text>
                        </Form.Group>

                        <Form.Group className="mb-3">
                            <Form.Label>Discipline (Optional)</Form.Label>
                            <Form.Select
                                value={discipline}
                                onChange={(e) => setDiscipline(e.target.value)}
                            >
                                <option value="">Select discipline (optional)</option>
                                <option value="computer_science">Computer Science</option>
                                <option value="mathematics">Mathematics</option>
                                <option value="engineering">Engineering</option>
                                <option value="business">Business</option>
                                <option value="humanities">Humanities</option>
                                <option value="sciences">Sciences</option>
                            </Form.Select>
                            <Form.Text className="text-muted">
                                Selecting a discipline helps Ellie understand your course better.
                            </Form.Text>
                        </Form.Group>

                        <Form.Group className="mb-3">
                            <Form.Label>Upload Course Materials (Optional)</Form.Label>
                            <Form.Control
                                type="file"
                                multiple
                                accept=".pdf,.pptx,.docx,.txt"
                                onChange={(e) => setFiles((e.target as HTMLInputElement).files)}
                            />
                            <Form.Text className="text-muted">
                                You can upload PDF, PowerPoint, Word, and text files (max 16MB each).
                            </Form.Text>
                        </Form.Group>
                    </Form>
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="secondary" onClick={handleClose}>
                        Cancel
                    </Button>
                    <Button
                        variant="primary"
                        onClick={handleSubmit}
                        disabled={isLoading}
                    >
                        {isLoading ? (
                            <>
                                <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                                Creating...
                            </>
                        ) : (
                            <>
                                <i className="bi bi-plus-lg me-1"></i> Create Course
                            </>
                        )}
                    </Button>
                </Modal.Footer>
            </Modal>
        </>
    );
};

export default CreateCourseCard; 