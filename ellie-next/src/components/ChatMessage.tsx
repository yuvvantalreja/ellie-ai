'use client';

import React from 'react';
import { formatDistanceToNow } from 'date-fns';

interface Reference {
    id: string;
    doc_id: string;
    source: string;
    page_or_slide?: number;
    title: string;
    subtitle?: string;
}

interface ChatMessageProps {
    content: string;
    role: 'user' | 'assistant';
    timestamp: number;
    references?: Reference[];
    onReferenceClick?: (reference: Reference) => void;
}

const ChatMessage: React.FC<ChatMessageProps> = ({
    content,
    role,
    timestamp,
    references = [],
    onReferenceClick
}) => {
    const messageClass = role === 'user' ? 'user-message' : 'assistant-message';
    const messageTime = formatDistanceToNow(new Date(timestamp * 1000), { addSuffix: true });

    // Process content to handle reference links
    const processContent = () => {
        if (!references.length) return content;

        let processedContent = content;

        // Sort references by ID length in descending order to avoid replacing substrings
        const sortedRefs = [...references].sort((a, b) => b.id.length - a.id.length);

        sortedRefs.forEach(ref => {
            // Create a regex to find reference markers like [ref1]
            const pattern = new RegExp(`\\[${ref.id}\\]`, 'g');

            // Replace with a highlighted version that uses data attributes
            processedContent = processedContent.replace(
                pattern,
                `<a class="reference-highlight" data-ref-id="${ref.id}" href="#ref-${ref.id}">[${ref.id}]</a>`
            );
        });

        return processedContent;
    };

    const handleReferenceClick = (e: React.MouseEvent) => {
        const target = e.target as HTMLElement;

        // Check if clicked element is a reference highlight
        if (target.classList.contains('reference-highlight') && onReferenceClick) {
            e.preventDefault();

            // Get the reference ID from the data attribute
            const refId = target.getAttribute('data-ref-id');
            if (!refId) return;

            // Find the reference in our list
            const reference = references.find(ref => ref.id === refId);
            if (reference) {
                onReferenceClick(reference);
            }
        }
    };

    // Process code blocks to remove backticks
    const cleanCodeBlocks = (text: string) => {
        return text.replace(/```([\s\S]*?)```/g, (match, codeContent) => {
            return `<pre><code>${codeContent.trim()}</code></pre>`;
        });
    };

    const finalContent = cleanCodeBlocks(processContent());

    return (
        <div className={`message ${messageClass}`}>
            <h5>{role === 'user' ? 'You' : 'Ellie'}</h5>
            <div
                className="message-content"
                dangerouslySetInnerHTML={{ __html: finalContent }}
                onClick={handleReferenceClick}
            />
            <div className="message-time">{messageTime}</div>

            {role === 'assistant' && references.length > 0 && (
                <div className="references">
                    <h6 className="references-title">References:</h6>
                    <ul className="references-list">
                        {references.map((ref) => (
                            <li key={ref.id} id={`ref-${ref.id}`}>
                                <a
                                    href="#"
                                    onClick={(e) => {
                                        e.preventDefault();
                                        if (onReferenceClick) onReferenceClick(ref);
                                    }}
                                    className="reference-item"
                                >
                                    {ref.id}: {ref.title} {ref.page_or_slide ? `(Page ${ref.page_or_slide})` : ''}
                                </a>
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
};

export default ChatMessage; 