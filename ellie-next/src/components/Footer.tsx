import React from 'react';
import { Container, Row, Col } from 'react-bootstrap';

const Footer: React.FC = () => {
    const currentYear = new Date().getFullYear();

    return (
        <footer className="footer text-center">
            <Container>
                <Row>
                    <Col md={12}>
                        <p><i className="bi bi-mortarboard-fill me-2"></i>Ellie - Carnegie Mellon University AI Teaching Assistant</p>
                        <p className="mb-0"><small>&copy; {currentYear} Carnegie Mellon University</small></p>
                    </Col>
                </Row>
            </Container>
        </footer>
    );
};

export default Footer; 