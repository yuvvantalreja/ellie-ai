import { NextRequest, NextResponse } from 'next/server';
import axios from 'axios';

export async function GET(request: NextRequest) {
    try {
        // Get course_id from query parameters
        const searchParams = request.nextUrl.searchParams;
        const courseId = searchParams.get('course_id');

        if (!courseId) {
            return NextResponse.json(
                { error: 'Course ID is required' },
                { status: 400 }
            );
        }

        // Get user ID from cookies
        const userId = request.cookies.get('user_id')?.value;
        if (!userId) {
            // If no user ID, return empty history
            return NextResponse.json({ history: [] });
        }

        // Get the backend URL from env or use default
        const backendUrl = process.env.BACKEND_URL || 'http://localhost:5000';

        // Forward the request to the Flask backend
        const response = await axios.get(`${backendUrl}/api/history`, {
            params: {
                course_id: courseId,
                user_id: userId
            }
        });

        // Return the response from the backend
        return NextResponse.json(response.data);
    } catch (error) {
        console.error('Error fetching history:', error);
        return NextResponse.json(
            { error: 'Failed to fetch history' },
            { status: 500 }
        );
    }
} 