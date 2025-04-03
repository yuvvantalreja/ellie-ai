import { NextRequest, NextResponse } from 'next/server';
import axios from 'axios';

export async function POST(request: NextRequest) {
    try {
        // Parse the request body
        const body = await request.json();
        const { course_id, discipline } = body;

        if (!course_id) {
            return NextResponse.json(
                { error: 'Course ID is required' },
                { status: 400 }
            );
        }

        // Get the backend URL from env or use default
        const backendUrl = process.env.BACKEND_URL || 'http://127.0.0.1:5001';

        // Forward the request to the Flask backend
        const response = await axios.post(`${backendUrl}/api/create_course`, {
            course_id,
            discipline: discipline || undefined
        });

        // Return the response from the backend
        return NextResponse.json(response.data);
    } catch (error: any) {
        console.error('Error creating course:', error.message);
        if (error.response) {
            console.error('Response status:', error.response.status);
            console.error('Response data:', error.response.data);
        }

        return NextResponse.json(
            { error: 'Failed to create course', message: error.message },
            { status: 500 }
        );
    }
} 