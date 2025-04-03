'use client';

import React from 'react';
import Link from 'next/link';
import { Navbar, Container, Nav } from 'react-bootstrap';

interface HeaderProps {
    courseId?: string;
}

const Header: React.FC<HeaderProps> = ({ courseId }) => {
    return (
        <header className="header text-center">
            <Container>
                <Navbar expand="lg" variant="dark" className="p-0">
                    <Link href="/" className="text-decoration-none">
                        <Navbar.Brand className="d-flex align-items-center">
                            <i className="bi bi-mortarboard-fill me-2"></i>
                            Ellie
                        </Navbar.Brand>
                    </Link>

                    {courseId && (
                        <div className="ms-3 text-white">
                            | <span className="ms-2">{courseId}</span>
                        </div>
                    )}

                    <Navbar.Toggle aria-controls="basic-navbar-nav" className="ms-auto" />

                    <Navbar.Collapse id="basic-navbar-nav">
                        <Nav className="ms-auto">
                            {courseId && (
                                <>
                                    <Link href="/" className="nav-link">
                                        <i className="bi bi-house-door me-1"></i> Home
                                    </Link>
                                    <Link href={`/course/${courseId}`} className="nav-link">
                                        <i className="bi bi-chat-dots me-1"></i> Chat
                                    </Link>
                                </>
                            )}
                        </Nav>
                    </Navbar.Collapse>
                </Navbar>

                {!courseId && (
                    <div className="py-3">
                        <h1 className="display-4">
                            <i className="bi bi-mortarboard-fill me-2"></i>Ellie
                        </h1>
                        <p className="lead">Carnegie Mellon University's AI Teaching Assistant</p>
                    </div>
                )}
            </Container>
        </header>
    );
};

export default Header; 