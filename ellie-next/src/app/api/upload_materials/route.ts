import { NextRequest, NextResponse } from 'next/server';
import axios from 'axios';
import FormData from 'form-data';
import { Readable } from 'stream';

export async function POST(request: NextRequest) {
    try {
        // Check if the request is multipart/form-data
        if (!request.headers.get('content-type')?.includes('multipart/form-data')) {
            return NextResponse.json(
                { error: 'Request must be multipart/form-data' },
                { status: 400 }
            );
        }

        // Parse the form data
        const formData = await request.formData();
        const courseId = formData.get('course_id');
        const files = formData.getAll('materials');

        if (!courseId) {
            return NextResponse.json(
                { error: 'Course ID is required' },
                { status: 400 }
            );
        }

        if (!files || files.length === 0) {
            return NextResponse.json(
                { error: 'No files uploaded' },
                { status: 400 }
            );
        }

        // Get the backend URL from env or use default
        const backendUrl = process.env.BACKEND_URL || 'http://localhost:5000';

        // Create a new FormData object to send to the backend
        const backendFormData = new FormData();
        backendFormData.append('course_id', courseId);

        // Add each file to the form data
        for (const file of files) {
            if (file instanceof File) {
                const arrayBuffer = await file.arrayBuffer();
                const buffer = Buffer.from(arrayBuffer);
                const stream = Readable.from(buffer);

                backendFormData.append('materials', stream, {
                    filename: file.name,
                    contentType: file.type,
                    knownLength: buffer.length
                });
            }
        }

        // Forward the request to the Flask backend
        const response = await axios.post(
            `${backendUrl}/api/upload_materials`,
            backendFormData,
            {
                headers: {
                    ...backendFormData.getHeaders()
                }
            }
        );

        // Return the response from the backend
        return NextResponse.json(response.data);
    } catch (error) {
        console.error('Error uploading materials:', error);
        return NextResponse.json(
            { error: 'Failed to upload materials' },
            { status: 500 }
        );
    }
} 