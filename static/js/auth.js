/**
 * Ellie - CMU AI Teaching Assistant
 * Firebase Authentication Integration
 */

// Firebase config will be injected by the server
let firebaseConfig = {};

// Initialize Firebase when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Fetch Firebase config from the server
    fetch('/api/firebase_config')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Initialize Firebase with the config
                firebaseConfig = data.config;
                initializeFirebase();
            } else {
                console.error('Failed to load Firebase config:', data.error);
            }
        })
        .catch(error => {
            console.error('Error fetching Firebase config:', error);
        });
});

// Initialize Firebase
function initializeFirebase() {
    if (!firebaseConfig.apiKey) {
        console.error('Firebase API key is missing');
        return;
    }

    // Initialize Firebase
    firebase.initializeApp(firebaseConfig);
    
    // Set up auth state change listener
    firebase.auth().onAuthStateChanged(function(user) {
        if (user) {
            console.log('User is signed in:', user.email);
            // The user is already being handled by the server-side session
        } else {
            console.log('User is signed out');
        }
    });
    
    // Set up Google sign-in button if it exists
    setupGoogleSignIn();
}

// Set up Google Sign-in
function setupGoogleSignIn() {
    console.log("Setting up Google Sign-in buttons");
    const googleLoginBtn = document.getElementById('googleLoginBtn');
    if (googleLoginBtn) {
        console.log("Google login button found");
        googleLoginBtn.addEventListener('click', function() {
            console.log("Google login button clicked");
            const provider = new firebase.auth.GoogleAuthProvider();
            provider.addScope('profile');
            provider.addScope('email');
            
            console.log("Starting Google sign-in popup");
            firebase.auth().signInWithPopup(provider)
                .then(function(result) {
                    console.log("Google sign-in successful", result);
                    // Get the Firebase user
                    const user = result.user;
                    
                    // Get the Firebase ID token (not the Google OAuth token)
                    return user.getIdToken().then(function(firebaseToken) {
                        console.log("Got Firebase ID token");
                        // Send the Firebase token to the server
                        console.log("Sending Firebase token to server for login");
                        return sendTokenToServer(firebaseToken);
                    });
                })
                .catch(function(error) {
                    console.error('Error signing in with Google:', error);
                    showAuthError(error.message);
                });
        });
    } else {
        console.log("Google login button NOT found");
    }
    
    const googleRegisterBtn = document.getElementById('googleRegisterBtn');
    if (googleRegisterBtn) {
        console.log("Google register button found");
        googleRegisterBtn.addEventListener('click', function() {
            console.log("Google register button clicked");
            const provider = new firebase.auth.GoogleAuthProvider();
            provider.addScope('profile');
            provider.addScope('email');
            
            console.log("Starting Google sign-in popup for registration");
            firebase.auth().signInWithPopup(provider)
                .then(function(result) {
                    console.log("Google sign-in for registration successful", result);
                    // Get the Firebase user
                    const user = result.user;
                    
                    // Get the Firebase ID token (not the Google OAuth token)
                    return user.getIdToken().then(function(firebaseToken) {
                        console.log("Got Firebase ID token");
                        // Send the Firebase token to the server with registration flag
                        console.log("Sending Firebase token to server for registration");
                        return sendTokenToServer(firebaseToken, true);
                    });
                })
                .catch(function(error) {
                    console.error('Error signing in with Google:', error);
                    showAuthError(error.message);
                });
        });
    } else {
        console.log("Google register button NOT found");
    }
}

// Send token to server
function sendTokenToServer(idToken, isRegistration = false) {
    const endpoint = isRegistration ? '/api/auth/google_register' : '/api/auth/google_login';
    console.log(`Sending token to ${endpoint}`);
    
    return fetch(endpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token: idToken })
    })
    .then(response => {
        console.log(`Response from ${endpoint}:`, response);
        return response.json();
    })
    .then(data => {
        console.log(`Data from ${endpoint}:`, data);
        if (data.success) {
            // Handle successful login/registration
            if (data.redirect) {
                console.log(`Redirecting to ${data.redirect}`);
                window.location.href = data.redirect;
            } else {
                console.log('Redirecting to home page');
                window.location.href = '/';
            }
        } else {
            // Handle error
            console.error(`Error from ${endpoint}:`, data.error);
            showAuthError(data.error);
        }
    })
    .catch(error => {
        console.error('Error sending token to server:', error);
        showAuthError('Server error. Please try again later.');
    });
}

// Show authentication error
function showAuthError(message) {
    if (typeof customError === 'function') {
        customError(message);
    } else {
        alert(message);
    }
}

// Handle email/password login if form exists
const loginForm = document.getElementById('loginForm');
if (loginForm) {
    loginForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        
        if (!email || !password) {
            showAuthError('Please enter both email and password');
            return;
        }
        
        // Show loading state
        const loginBtn = document.getElementById('loginBtn');
        const originalBtnText = loginBtn.innerHTML;
        loginBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Signing in...';
        loginBtn.disabled = true;
        
        // Submit form normally (server-side handling)
        loginForm.submit();
    });
}

// Handle email/password registration if form exists
const registerForm = document.getElementById('registerForm');
if (registerForm) {
    registerForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const name = document.getElementById('name').value;
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        const role = document.querySelector('input[name="role"]:checked').value;
        
        if (!name || !email || !password || !role) {
            showAuthError('Please fill in all fields');
            return;
        }
        
        if (password.length < 6) {
            showAuthError('Password must be at least 6 characters long');
            return;
        }
        
        // Show loading state
        const registerBtn = document.getElementById('registerBtn');
        const originalBtnText = registerBtn.innerHTML;
        registerBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Creating account...';
        registerBtn.disabled = true;
        
        // Submit form normally (server-side handling)
        registerForm.submit();
    });
} 