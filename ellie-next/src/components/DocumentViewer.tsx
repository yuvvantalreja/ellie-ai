'use client';

import React, { useState } from 'react';
import { Card, Button, Spinner } from 'react-bootstrap';
import axios from 'axios';

interface Reference {
    id: string;
    doc_id: string;
    source: string;
    page_or_slide?: number;
    title: string;
    subtitle?: string;
}

interface DocumentViewerProps {
    courseId: string;
    isOpen: boolean;
    onClose: () => void;
}

const DocumentViewer: React.FC<DocumentViewerProps> = ({
    courseId,
    isOpen,
    onClose
}) => {
    const [currentDocument, setCurrentDocument] = useState<{
        docId: string;
        title: string;
        page: number;
        totalPages: number;
        fileType: string;
    } | null>(null);

    const [content, setContent] = useState<string>('');
    const [imageUrl, setImageUrl] = useState<string>('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const loadDocument = async (reference: Reference) => {
        setLoading(true);
        setError(null);

        try {
            // Get document metadata
            const metadataResponse = await axios.get(`/api/document/${courseId}/${reference.doc_id}`, {
                params: {
                    page: reference.page_or_slide
                }
            });

            if (metadataResponse.data.error) {
                throw new Error(metadataResponse.data.error);
            }

            const metadata = metadataResponse.data;

            setCurrentDocument({
                docId: reference.doc_id,
                title: metadata.title || reference.title,
                page: metadata.page || metadata.slide || 1,
                totalPages: metadata.total_pages || metadata.total_slides || 1,
                fileType: metadata.file_type
            });

            // Load content based on file type
            if (metadata.file_type === 'pdf') {
                // Get image of PDF page
                setImageUrl(`/api/document/render/${courseId}/${reference.doc_id}?page=${reference.page_or_slide || 1}`);

                // Get text content
                const contentResponse = await axios.get(`/api/document/content/${courseId}/${reference.doc_id}`, {
                    params: { page: reference.page_or_slide }
                });

                if (contentResponse.data && contentResponse.data.content) {
                    setContent(contentResponse.data.content);
                }
            } else {
                // Handle other file types
                const contentResponse = await axios.get(`/api/document/content/${courseId}/${reference.doc_id}`, {
                    params: {
                        page: reference.page_or_slide,
                        slide: reference.page_or_slide
                    }
                });

                if (contentResponse.data && contentResponse.data.content) {
                    setContent(contentResponse.data.content);
                }
            }
        } catch (err) {
            console.error('Error loading document:', err);
            setError('Failed to load document. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const navigatePage = (delta: number) => {
        if (!currentDocument) return;

        const newPage = currentDocument.page + delta;

        if (newPage >= 1 && newPage <= currentDocument.totalPages) {
            loadDocument({
                id: 'ref',
                doc_id: currentDocument.docId,
                source: '',
                page_or_slide: newPage,
                title: currentDocument.title
            });
        }
    };

    const downloadDocument = async () => {
        if (!currentDocument) return;

        try {
            window.open(`/api/document/download/${courseId}/${currentDocument.docId}`, '_blank');
        } catch (err) {
            console.error('Error downloading document:', err);
            setError('Failed to download document. Please try again.');
        }
    };

    return (
        <div className={`document-viewer ${isOpen ? 'open' : ''}`}>
            <Card className="h-100">
                <Card.Header className="d-flex justify-content-between align-items-center">
                    <h5 className="mb-0">
                        {currentDocument ? currentDocument.title : 'Document Viewer'}
                    </h5>
                    <Button variant="link" className="p-0 text-dark" onClick={onClose}>
                        <i className="bi bi-x-lg"></i>
                    </Button>
                </Card.Header>

                <Card.Body className="d-flex flex-column overflow-hidden">
                    {loading ? (
                        <div className="text-center my-5">
                            <Spinner animation="border" role="status" variant="primary" />
                            <p className="mt-3">Loading document...</p>
                        </div>
                    ) : error ? (
                        <div className="alert alert-danger m-3">
                            <i className="bi bi-exclamation-triangle-fill me-2"></i>
                            {error}
                        </div>
                    ) : currentDocument ? (
                        <div className="document-content flex-grow-1 overflow-auto">
                            {imageUrl && (
                                <div className="text-center mb-4">
                                    <img
                                        src={imageUrl}
                                        alt={`Page ${currentDocument.page}`}
                                        className="img-fluid border rounded shadow-sm"
                                        loading="lazy"
                                    />
                                </div>
                            )}

                            {content && (
                                <div className="content-text mt-3">
                                    <h6 className="text-muted mb-2">Text Content:</h6>
                                    <pre className="content-pre">{content}</pre>
                                </div>
                            )}
                        </div>
                    ) : (
                        <div className="text-center text-muted my-5">
                            <div className="mb-3">
                                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <path d="M14 2H6C5.46957 2 4.96086 2.21071 4.58579 2.58579C4.21071 2.96086 4 3.46957 4 4V20C4 20.5304 4.21071 21.0391 4.58579 21.4142C4.96086 21.7893 5.46957 22 6 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V8L14 2Z" stroke="#63666a" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                    <path d="M14 2V8H20" stroke="#63666a" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                    <path d="M16 13H8" stroke="#63666a" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                    <path d="M16 17H8" stroke="#63666a" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                    <path d="M10 9H9H8" stroke="#63666a" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                </svg>
                            </div>
                            <p className="mt-3">Select a reference to view document</p>
                        </div>
                    )}
                </Card.Body>

                {currentDocument && (
                    <Card.Footer className="bg-white border-top">
                        <div className="d-flex justify-content-between align-items-center">
                            <div className="pagination-controls">
                                <Button
                                    variant="outline-secondary"
                                    size="sm"
                                    onClick={() => navigatePage(-1)}
                                    disabled={!currentDocument || currentDocument.page <= 1}
                                    className="rounded-circle"
                                    style={{ width: '32px', height: '32px', padding: 0 }}
                                >
                                    <i className="bi bi-chevron-left"></i>
                                </Button>
                                <span className="mx-2">
                                    Page {currentDocument.page} of {currentDocument.totalPages}
                                </span>
                                <Button
                                    variant="outline-secondary"
                                    size="sm"
                                    onClick={() => navigatePage(1)}
                                    disabled={!currentDocument || currentDocument.page >= currentDocument.totalPages}
                                    className="rounded-circle"
                                    style={{ width: '32px', height: '32px', padding: 0 }}
                                >
                                    <i className="bi bi-chevron-right"></i>
                                </Button>
                            </div>

                            <Button
                                variant="outline-primary"
                                size="sm"
                                onClick={downloadDocument}
                                className="rounded-pill"
                            >
                                <i className="bi bi-download me-1"></i> Download
                            </Button>
                        </div>
                    </Card.Footer>
                )}
            </Card>
        </div>
    );
};

export default DocumentViewer; 