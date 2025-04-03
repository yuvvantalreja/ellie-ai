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
        const question = formData.get('question');
        const image = formData.get('image');

        if (!courseId) {
            return NextResponse.json(
                { error: 'Course ID is required' },
                { status: 400 }
            );
        }

        if (!image || !(image instanceof File)) {
            return NextResponse.json(
                { error: 'Image is required' },
                { status: 400 }
            );
        }

        // Get user ID from cookies
        const userId = request.cookies.get('user_id')?.value;

        // Get the backend URL from env or use default
        const backendUrl = process.env.BACKEND_URL || 'http://localhost:5000';

        // Create a new FormData object to send to the backend
        const backendFormData = new FormData();
        backendFormData.append('course_id', courseId);

        if (question) {
            backendFormData.append('question', question);
        }

        if (userId) {
            backendFormData.append('user_id', userId);
        }

        // Add the image to the form data
        const arrayBuffer = await image.arrayBuffer();
        const buffer = Buffer.from(arrayBuffer);
        const stream = Readable.from(buffer);

        backendFormData.append('image', stream, {
            filename: image.name,
            contentType: image.type,
            knownLength: buffer.length
        });

        // Forward the request to the Flask backend
        const response = await axios.post(
            `${backendUrl}/api/ask_with_image`,
            backendFormData,
            {
                headers: {
                    ...backendFormData.getHeaders()
                }
            }
        );

        // Create the response
        const nextResponse = NextResponse.json(response.data);

        // Set the user_id cookie if it doesn't exist and we have a userId
        if (!request.cookies.has('user_id') && userId) {
            nextResponse.cookies.set('user_id', userId, {
                httpOnly: true,
                maxAge: 60 * 60 * 24 * 30, // 30 days
                path: '/'
            });
        }

        return nextResponse;
    } catch (error) {
        console.error('Error processing image question:', error);
        return NextResponse.json(
            { error: 'Failed to process image question' },
            { status: 500 }
        );
    }
} 