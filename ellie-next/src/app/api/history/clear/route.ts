import { NextRequest, NextResponse } from 'next/server';
import axios from 'axios';

export async function POST(request: NextRequest) {
    try {
        // Parse the request body
        const body = await request.json();
        const { course_id } = body;

        if (!course_id) {
            return NextResponse.json(
                { error: 'Course ID is required' },
                { status: 400 }
            );
        }

        // Get user ID from cookies
        const userId = request.cookies.get('user_id')?.value;
        if (!userId) {
            // If no user ID, return success (nothing to clear)
            return NextResponse.json({ success: true });
        }

        // Get the backend URL from env or use default
        const backendUrl = process.env.BACKEND_URL || 'http://localhost:5000';

        // Forward the request to the Flask backend
        const response = await axios.post(`${backendUrl}/api/history/clear`, {
            course_id,
            user_id: userId
        });

        // Return the response from the backend
        return NextResponse.json(response.data);
    } catch (error) {
        console.error('Error clearing history:', error);
        return NextResponse.json(
            { error: 'Failed to clear history' },
            { status: 500 }
        );
    }
} 