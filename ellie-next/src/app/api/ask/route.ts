import { NextRequest, NextResponse } from 'next/server';
import axios from 'axios';
import { v4 as uuidv4 } from 'uuid';

export async function POST(request: NextRequest) {
    try {
        // Parse the request body
        const body = await request.json();
        const { course_id, question } = body;

        if (!course_id || !question) {
            return NextResponse.json(
                { error: 'Missing required parameters' },
                { status: 400 }
            );
        }

        // Get user ID from cookies or create a new one
        let userId = request.cookies.get('user_id')?.value;
        if (!userId) {
            userId = uuidv4();
        }

        // Get the backend URL from env or use default
        const backendUrl = process.env.BACKEND_URL || 'http://localhost:5000';

        // Forward the request to the Flask backend
        const response = await axios.post(`${backendUrl}/api/ask`, {
            course_id,
            question,
            user_id: userId
        });

        // Create the response
        const nextResponse = NextResponse.json(response.data);

        // Set the user_id cookie if it doesn't exist
        if (!request.cookies.has('user_id')) {
            nextResponse.cookies.set('user_id', userId, {
                httpOnly: true,
                maxAge: 60 * 60 * 24 * 30, // 30 days
                path: '/'
            });
        }

        return nextResponse;
    } catch (error) {
        console.error('Error in ask API:', error);
        return NextResponse.json(
            { error: 'Failed to process request' },
            { status: 500 }
        );
    }
} 