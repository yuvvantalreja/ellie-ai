/**
 * Ellie - CMU AI Teaching Assistant
 * Main JavaScript functionality
 */

// Wait for the DOM to be loaded
document.addEventListener('DOMContentLoaded', function() {
    
    // Add smooth scroll behavior
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });

    // Add animation to cards
    const cards = document.querySelectorAll('.card');
    if (cards.length > 0) {
        cards.forEach(card => {
            card.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-10px)';
                this.style.boxShadow = '0 15px 30px rgba(0,0,0,0.1)';
            });
            
            card.addEventListener('mouseleave', function() {
                this.style.transform = 'translateY(0)';
                this.style.boxShadow = '0 5px 15px rgba(0,0,0,0.05)';
            });
        });
    }

    // Add toast notification function
    window.showToast = function(message, type = 'info') {
        // Create toast container if it doesn't exist
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.style.position = 'fixed';
            toastContainer.style.top = '20px';
            toastContainer.style.right = '20px';
            toastContainer.style.zIndex = '9999';
            document.body.appendChild(toastContainer);
        }
        
        // Create toast
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.style.minWidth = '250px';
        toast.style.backgroundColor = type === 'error' ? '#c41230' : 
                                       type === 'success' ? '#198754' : '#0d6efd';
        toast.style.color = 'white';
        toast.style.padding = '15px';
        toast.style.marginBottom = '10px';
        toast.style.borderRadius = '4px';
        toast.style.boxShadow = '0 4px 8px rgba(0,0,0,0.1)';
        toast.style.animation = 'fade-in 0.3s ease-in-out';
        
        // Add animation keyframes
        if (!document.getElementById('toast-styles')) {
            const style = document.createElement('style');
            style.id = 'toast-styles';
            style.textContent = `
                @keyframes fade-in {
                    from { opacity: 0; transform: translateY(-20px); }
                    to { opacity: 1; transform: translateY(0); }
                }
                @keyframes fade-out {
                    from { opacity: 1; transform: translateY(0); }
                    to { opacity: 0; transform: translateY(-20px); }
                }
            `;
            document.head.appendChild(style);
        }
        
        // Set content
        toast.innerHTML = `
            <div style="display: flex; align-items: center;">
                <div style="margin-right: 10px;">
                    <i class="bi bi-${type === 'error' ? 'exclamation-circle' : 
                                     type === 'success' ? 'check-circle' : 'info-circle'}"></i>
                </div>
                <div>${message}</div>
            </div>
        `;
        
        // Add to container
        toastContainer.appendChild(toast);
        
        // Remove after 5 seconds
        setTimeout(() => {
            toast.style.animation = 'fade-out 0.3s ease-in-out';
            setTimeout(() => {
                toastContainer.removeChild(toast);
            }, 300);
        }, 5000);
    };

    // Replace browser alerts with custom toasts
    window.customAlert = function(message) {
        window.showToast(message, 'info');
    };

    // Replace error alerts
    window.customError = function(message) {
        window.showToast(message, 'error');
    };

    // Replace success alerts
    window.customSuccess = function(message) {
        window.showToast(message, 'success');
    };

    // Initialize document viewer if on chat page
    if (document.getElementById('documentSide')) {
        const courseId = document.querySelector('[data-course-id]')?.dataset.courseId;
        window.documentViewer = new DocumentViewer({ courseId });
    }
});

// Document Viewer Component
class DocumentViewer {
    constructor(options = {}) {
        this.documentSide = document.getElementById(options.documentContainerId || 'documentSide');
        this.documentContent = document.getElementById(options.contentId || 'documentContent');
        this.documentTitle = document.getElementById(options.titleId || 'documentTitle');
        this.pageInfo = document.getElementById(options.pageInfoId || 'pageInfo');
        this.prevBtn = document.getElementById(options.prevBtnId || 'prevBtn');
        this.nextBtn = document.getElementById(options.nextBtnId || 'nextBtn');
        this.downloadBtn = document.getElementById(options.downloadBtnId || 'downloadBtn');
        this.toggleBtn = document.getElementById(options.toggleBtnId || 'toggleDocumentBtn');
        this.closeBtn = document.getElementById(options.closeBtnId || 'closeDocumentBtn');
        
        this.courseId = options.courseId || '';
        
        // Current document state
        this.currentDocument = {
            courseId: '',
            docId: '',
            page: 1,
            totalPages: 1,
            filePath: '',
            fileName: '',
            fileType: ''
        };
        
        this.init();
    }
    
    init() {
        // Initialize event listeners
        if (this.toggleBtn) {
            this.toggleBtn.addEventListener('click', () => this.toggleDocumentPanel());
        }
        
        if (this.closeBtn) {
            this.closeBtn.addEventListener('click', () => this.hideDocumentPanel());
        }
        
        if (this.prevBtn) {
            this.prevBtn.addEventListener('click', () => this.navigatePage(-1));
        }
        
        if (this.nextBtn) {
            this.nextBtn.addEventListener('click', () => this.navigatePage(1));
        }
        
        if (this.downloadBtn) {
            this.downloadBtn.addEventListener('click', () => this.downloadDocument());
        }
    }
    
    toggleDocumentPanel() {
        if (this.documentSide) {
            this.documentSide.classList.toggle('active');
        }
    }
    
    showDocumentPanel() {
        if (this.documentSide) {
            this.documentSide.classList.add('active');
        }
    }
    
    hideDocumentPanel() {
        if (this.documentSide) {
            this.documentSide.classList.remove('active');
        }
    }
    
    navigatePage(delta) {
        const newPage = this.currentDocument.page + delta;
        if (newPage >= 1 && newPage <= this.currentDocument.totalPages) {
            this.currentDocument.page = newPage;
            this.loadDocumentPage();
        }
    }
    
    updateNavigation() {
        if (this.prevBtn) {
            this.prevBtn.disabled = this.currentDocument.page <= 1;
        }
        
        if (this.nextBtn) {
            this.nextBtn.disabled = this.currentDocument.page >= this.currentDocument.totalPages;
        }
        
        if (this.pageInfo) {
            if (this.currentDocument.fileType === 'pdf') {
                this.pageInfo.textContent = `Page ${this.currentDocument.page} of ${this.currentDocument.totalPages}`;
            } else if (this.currentDocument.fileType === 'pptx') {
                this.pageInfo.textContent = `Slide ${this.currentDocument.page} of ${this.currentDocument.totalPages}`;
            } else {
                this.pageInfo.textContent = '';
            }
        }
    }
    
    setLoading() {
        if (this.documentContent) {
            this.documentContent.innerHTML = `
                <div class="text-center my-5">
                    <div class="spinner-border text-primary" role="status"></div>
                    <p class="mt-3">Loading content...</p>
                </div>
            `;
        }
    }
    
    showError(message) {
        if (this.documentContent) {
            this.documentContent.innerHTML = `
                <div class="alert alert-danger">
                    ${message}
                </div>
            `;
        }
    }
    
    async loadDocument(documentInfo) {
        try {
            this.showDocumentPanel();
            this.setLoading();
            
            const courseId = documentInfo.courseId || this.courseId;
            const docId = documentInfo.docId;
            const pageOrSlide = documentInfo.page || documentInfo.slide || 1;
            
            if (!docId) {
                this.showError('Document ID is required');
                return;
            }
            
            // Get document metadata
            const response = await fetch(`/api/document/${courseId}/${docId}?page=${pageOrSlide}`);
            const data = await response.json();
            
            if (data.error) {
                this.showError(data.error);
                return;
            }
            
            // Update current document state
            this.currentDocument = {
                courseId: courseId,
                docId: docId,
                page: data.page || data.slide || 1,
                totalPages: data.total_pages || data.total_slides || 1,
                filePath: data.file_path,
                fileName: data.file_name,
                fileType: data.file_type,
                title: data.title
            };
            
            // Update UI
            if (this.documentTitle) {
                this.documentTitle.textContent = data.title || data.file_name;
            }
            
            this.updateNavigation();
            this.loadDocumentPage();
            
        } catch (error) {
            this.showError(`Error loading document: ${error.message}`);
        }
    }
    
    async loadDocumentPage() {
        try {
            this.updateNavigation();
            this.setLoading();
            
            const { courseId, docId, page, fileType } = this.currentDocument;
            
            if (fileType === 'pdf') {
                await this.loadPdfPage(courseId, docId, page);
            } else if (fileType === 'pptx') {
                await this.loadSlide(courseId, docId, page);
            } else {
                this.documentContent.innerHTML = '<div class="alert alert-warning">Preview not available for this file type</div>';
            }
        } catch (error) {
            this.showError(`Error loading content: ${error.message}`);
        }
    }
    
    async loadPdfPage(courseId, docId, page) {
        // Load PDF as image
        const imgElement = document.createElement('img');
        imgElement.className = 'document-img';
        imgElement.src = `/api/document/render/${courseId}/${docId}?page=${page}`;
        imgElement.alt = `Page ${page}`;
        
        // Clear and add to container
        this.documentContent.innerHTML = '';
        this.documentContent.appendChild(imgElement);
        
        // Add text content below the image
        try {
            const response = await fetch(`/api/document/content/${courseId}/${docId}?page=${page}`);
            const data = await response.json();
            
            if (!data.error && data.content) {
                const textDiv = document.createElement('div');
                textDiv.className = 'mt-4 p-3 bg-light rounded';
                textDiv.innerHTML = `<h6>Text Content:</h6><pre>${data.content}</pre>`;
                this.documentContent.appendChild(textDiv);
            }
        } catch (error) {
            console.error('Error fetching text content:', error);
        }
    }
    
    async loadSlide(courseId, docId, slide) {
        try {
            const response = await fetch(`/api/document/content/${courseId}/${docId}?slide=${slide}`);
            const data = await response.json();
            
            if (data.error) {
                this.showError(data.error);
                return;
            }
            
            const slideContent = document.createElement('div');
            slideContent.className = 'slide-content p-4 bg-white rounded shadow-sm';
            
            if (data.title) {
                const titleElement = document.createElement('h3');
                titleElement.className = 'slide-title mb-4';
                titleElement.textContent = data.title;
                slideContent.appendChild(titleElement);
            }
            
            const contentElement = document.createElement('div');
            contentElement.className = 'slide-text';
            contentElement.innerHTML = data.content.replace(/\n/g, '<br>');
            slideContent.appendChild(contentElement);
            
            this.documentContent.innerHTML = '';
            this.documentContent.appendChild(slideContent);
        } catch (error) {
            this.showError(`Error loading slide: ${error.message}`);
        }
    }
    
    downloadDocument() {
        if (this.currentDocument.filePath) {
            const link = document.createElement('a');
            link.href = `/api/document/download/${this.currentDocument.courseId}/${this.currentDocument.docId}`;
            link.download = this.currentDocument.fileName;
            link.click();
        }
    }
} 