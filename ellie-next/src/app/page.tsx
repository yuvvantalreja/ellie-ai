'use client';

import React, { useEffect, useState } from 'react';
import { Container, Row, Col, Card } from 'react-bootstrap';
import axios from 'axios';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import CourseCard from '@/components/CourseCard';
import CreateCourseCard from '@/components/CreateCourseCard';

export default function Home() {
  const [courses, setCourses] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchCourses = async () => {
      try {
        const response = await axios.get('/api/courses');
        setCourses(response.data.courses || []);
      } catch (err) {
        console.error('Error fetching courses:', err);
        setError('Failed to load courses. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchCourses();
  }, []);

  return (
    <main>
      <Header />

      <div className="container main-container">
        <Row className="mb-5">
          <Col md={8} className="offset-md-2">
            <Card>
              <Card.Body className="text-center p-4">
                <h2 className="mb-3">Welcome to Ellie</h2>
                <p className="fs-5">I'm your personal AI teaching assistant for Carnegie Mellon University courses. I can help answer questions, explain concepts, and guide you through your coursework.</p>
                <p className="fs-5 mb-4">Select a course below to start chatting or create a new course.</p>
              </Card.Body>
            </Card>
          </Col>
        </Row>

        <h2 className="text-center mb-4">
          <i className="bi bi-book me-2"></i>Available Courses
        </h2>

        <Row id="coursesList">
          {loading ? (
            <Col className="text-center py-5">
              <div className="spinner-border text-primary" role="status">
                <span className="visually-hidden">Loading...</span>
              </div>
              <p className="mt-3">Loading courses...</p>
            </Col>
          ) : error ? (
            <Col className="text-center">
              <div className="alert alert-danger">
                <i className="bi bi-exclamation-triangle me-2"></i>
                {error}
              </div>
            </Col>
          ) : (
            <>
              {courses.map((course) => (
                <CourseCard key={course} courseId={course} />
              ))}

              <CreateCourseCard />

              {courses.length === 0 && (
                <Col xs={12} className="text-center">
                  <div className="alert alert-info p-5">
                    <i className="bi bi-info-circle fs-4 me-2"></i>
                    <p className="mb-0 fs-5">Click "Create New Course" to get started!</p>
                  </div>
                </Col>
              )}
            </>
          )}
        </Row>
      </div>

      <Footer />
    </main>
  );
}
