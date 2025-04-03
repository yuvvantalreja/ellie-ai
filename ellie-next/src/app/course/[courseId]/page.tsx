'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useParams } from 'next/navigation';
import { Container, Row, Col, Button, Spinner } from 'react-bootstrap';
import axios from 'axios';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import ChatMessage from '@/components/ChatMessage';
import ChatInput from '@/components/ChatInput';
import DocumentViewer from '@/components/DocumentViewer';

interface Message {
    role: 'user' | 'assistant';
    content: string;
    timestamp: number;
    references?: any[];
}

interface Reference {
    id: string;
    doc_id: string;
    source: string;
    page_or_slide?: number;
    title: string;
    subtitle?: string;
}

export default function CoursePage() {
    const params = useParams();
    const courseId = params.courseId as string;

    const [messages, setMessages] = useState<Message[]>([]);
    const [loading, setLoading] = useState(true);
    const [thinking, setThinking] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [documentViewerOpen, setDocumentViewerOpen] = useState(false);
    const [selectedReference, setSelectedReference] = useState<Reference | null>(null);

    const messagesEndRef = useRef<HTMLDivElement>(null);

    // Fetch chat history when the page loads
    useEffect(() => {
        const fetchHistory = async () => {
            try {
                setLoading(true);
                const response = await axios.get(`/api/history?course_id=${courseId}`);

                if (response.data.history) {
                    setMessages(response.data.history);
                }
            } catch (err) {
                console.error('Error fetching chat history:', err);
                setError('Failed to load chat history. Please try again later.');
            } finally {
                setLoading(false);
            }
        };

        if (courseId) {
            fetchHistory();
        }
    }, [courseId]);

    // Scroll to bottom when messages change
    useEffect(() => {
        if (messagesEndRef.current) {
            messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [messages]);

    const handleSendMessage = async (message: string, file: File | null = null) => {
        if (!message.trim() && !file) return;

        // Add user message to the UI immediately
        const userMessage: Message = {
            role: 'user',
            content: message,
            timestamp: Math.floor(Date.now() / 1000)
        };

        setMessages((prevMessages) => [...prevMessages, userMessage]);
        setThinking(true);

        try {
            let response;

            if (file) {
                // If there's a file, use the image upload endpoint
                const formData = new FormData();
                formData.append('course_id', courseId);
                formData.append('question', message);
                formData.append('image', file);

                response = await axios.post('/api/ask_with_image', formData);
            } else {
                // Regular text question
                response = await axios.post('/api/ask', {
                    course_id: courseId,
                    question: message
                });
            }

            if (response.data.error) {
                throw new Error(response.data.error);
            }

            // Add assistant response to the UI
            const assistantMessage: Message = {
                role: 'assistant',
                content: response.data.answer,
                timestamp: Math.floor(Date.now() / 1000),
                references: response.data.references
            };

            setMessages((prevMessages) => [...prevMessages, assistantMessage]);
        } catch (err) {
            console.error('Error sending message:', err);
            setError('Failed to send message. Please try again.');

            // Add error message
            const errorMessage: Message = {
                role: 'assistant',
                content: 'Sorry, I encountered an error processing your request. Please try again.',
                timestamp: Math.floor(Date.now() / 1000)
            };

            setMessages((prevMessages) => [...prevMessages, errorMessage]);
        } finally {
            setThinking(false);
        }
    };

    const handleClearChat = async () => {
        try {
            await axios.post('/api/history/clear', { course_id: courseId });
            setMessages([]);
        } catch (err) {
            console.error('Error clearing chat history:', err);
            setError('Failed to clear chat history. Please try again.');
        }
    };

    const handleReferenceClick = (reference: Reference) => {
        setSelectedReference(reference);
        setDocumentViewerOpen(true);
    };

    return (
        <main className="d-flex flex-column min-vh-100">
            <Header courseId={courseId} />

            <Container fluid className="flex-grow-1 d-flex">
                <Row className="flex-grow-1 w-100">
                    <Col md={documentViewerOpen ? 8 : 12} className="chat-column">
                        <div className="chat-container">
                            <div className="d-flex justify-content-between align-items-center mb-3">
                                <h2>
                                    <i className="bi bi-chat-dots me-2"></i>
                                    Chat with Ellie
                                </h2>

                                <Button
                                    variant="outline-secondary"
                                    size="sm"
                                    onClick={handleClearChat}
                                    disabled={loading || thinking || messages.length === 0}
                                >
                                    <i className="bi bi-trash me-1"></i> Clear Chat
                                </Button>
                            </div>

                            <div className="messages-container card">
                                {loading ? (
                                    <div className="text-center p-5">
                                        <Spinner animation="border" role="status" />
                                        <p className="mt-3">Loading chat history...</p>
                                    </div>
                                ) : error ? (
                                    <div className="alert alert-danger m-3">
                                        <i className="bi bi-exclamation-triangle-fill me-2"></i>
                                        {error}
                                    </div>
                                ) : messages.length === 0 ? (
                                    <div className="text-center text-muted p-5">
                                        <i className="bi bi-chat-square-text display-4"></i>
                                        <p className="mt-3">Start a conversation with Ellie, your AI teaching assistant for {courseId}.</p>
                                    </div>
                                ) : (
                                    <div className="p-3">
                                        {messages.map((msg, index) => (
                                            <ChatMessage
                                                key={index}
                                                content={msg.content}
                                                role={msg.role}
                                                timestamp={msg.timestamp}
                                                references={msg.references}
                                                onReferenceClick={handleReferenceClick}
                                            />
                                        ))}

                                        {thinking && (
                                            <div className="thinking">
                                                <span>Ellie is thinking</span>
                                                <div className="dots">
                                                    <div className="dot"></div>
                                                    <div className="dot"></div>
                                                    <div className="dot"></div>
                                                </div>
                                            </div>
                                        )}

                                        <div ref={messagesEndRef} />
                                    </div>
                                )}
                            </div>

                            <div className="input-container mt-3">
                                <ChatInput
                                    onSendMessage={handleSendMessage}
                                    disabled={thinking}
                                />
                            </div>
                        </div>
                    </Col>

                    {documentViewerOpen && (
                        <Col md={4} className="document-column">
                            <DocumentViewer
                                courseId={courseId}
                                isOpen={documentViewerOpen}
                                onClose={() => setDocumentViewerOpen(false)}
                            />
                        </Col>
                    )}
                </Row>
            </Container>

            <Footer />
        </main>
    );
} 