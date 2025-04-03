'use client';

import React, { useState, useRef } from 'react';
import { Button, Form, InputGroup } from 'react-bootstrap';

interface ChatInputProps {
    onSendMessage: (message: string, file?: File | null) => void;
    disabled?: boolean;
}

const ChatInput: React.FC<ChatInputProps> = ({ onSendMessage, disabled = false }) => {
    const [message, setMessage] = useState('');
    const [file, setFile] = useState<File | null>(null);
    const [showImageUpload, setShowImageUpload] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();

        if (message.trim() || file) {
            onSendMessage(message, file);
            setMessage('');
            setFile(null);
            setShowImageUpload(false);
        }
    };

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files.length > 0) {
            setFile(e.target.files[0]);
        }
    };

    const triggerFileUpload = () => {
        if (fileInputRef.current) {
            fileInputRef.current.click();
        }
    };

    return (
        <Form onSubmit={handleSubmit}>
            {showImageUpload && (
                <div className="image-upload-section mb-2">
                    <input
                        type="file"
                        className="d-none"
                        ref={fileInputRef}
                        accept="image/*"
                        onChange={handleFileChange}
                    />

                    <div className="d-flex align-items-center">
                        <Button
                            variant="outline-secondary"
                            size="sm"
                            onClick={triggerFileUpload}
                            className="me-2"
                        >
                            {file ? 'Change Image' : 'Upload Image'}
                        </Button>

                        {file && (
                            <>
                                <span className="file-name me-2">
                                    {file.name} ({(file.size / 1024).toFixed(1)} KB)
                                </span>
                                <Button
                                    variant="outline-danger"
                                    size="sm"
                                    onClick={() => setFile(null)}
                                >
                                    <i className="bi bi-x"></i>
                                </Button>
                            </>
                        )}
                    </div>
                </div>
            )}

            <InputGroup className="mb-3">
                <Form.Control
                    placeholder="Type your message here..."
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    aria-label="Type your message"
                    disabled={disabled}
                />

                <Button
                    variant="outline-secondary"
                    onClick={() => setShowImageUpload(!showImageUpload)}
                    title={showImageUpload ? "Hide image upload" : "Show image upload"}
                >
                    <i className="bi bi-image"></i>
                </Button>

                <Button
                    variant="primary"
                    type="submit"
                    disabled={disabled || (!message.trim() && !file)}
                >
                    <i className="bi bi-send-fill"></i>
                </Button>
            </InputGroup>
        </Form>
    );
};

export default ChatInput; 