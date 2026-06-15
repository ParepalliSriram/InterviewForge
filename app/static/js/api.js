// API Client for InterviewFroge backend

const API_BASE = "/api";

async function request(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    
    // Set credentials so session cookies are automatically sent and received
    options.credentials = 'include';
    
    if (options.body && typeof options.body === 'object') {
        options.body = JSON.stringify(options.body);
        options.headers = {
            'Content-Type': 'application/json',
            ...(options.headers || {})
        };
    }

    try {
        const response = await fetch(url, options);
        let data = null;
        try {
            data = await response.json();
        } catch (e) {
            // response was not JSON or empty
        }

        if (!response.ok) {
            let errorMsg = `HTTP error ${response.status}`;
            if (data) {
                if (data.detail) {
                    if (typeof data.detail === 'string') {
                        errorMsg = data.detail;
                    } else if (Array.isArray(data.detail)) {
                        errorMsg = data.detail.map(err => err.msg || JSON.stringify(err)).join(', ');
                    } else if (typeof data.detail === 'object') {
                        errorMsg = data.detail.message || data.detail.msg || JSON.stringify(data.detail);
                    } else {
                        errorMsg = String(data.detail);
                    }
                } else if (data.message) {
                    errorMsg = data.message;
                } else if (data.error) {
                    errorMsg = typeof data.error === 'string' ? data.error : JSON.stringify(data.error);
                }
            }
            throw new Error(errorMsg);
        }

        return data;
    } catch (error) {
        console.error(`API Request failed on ${endpoint}:`, error);
        throw error;
    }
}

const API = {
    auth: {
        register: (username, email, password) => 
            request('/auth/register', {
                method: 'POST',
                body: { username, email, password }
            }),
        login: (email, password) => 
            request('/auth/login', {
                method: 'POST',
                body: { email, password }
            }),
        logout: () => 
            request('/auth/logout', { method: 'POST' }),
        me: () => 
            request('/auth/me', { method: 'GET' }),
        updateUsername: (username) =>
            request('/auth/update-username', {
                method: 'POST',
                body: { username }
            })
    },
    interview: {
        setup: (role, experience, interview_type, resume_text = null) => 
            request('/interview/setup', {
                method: 'POST',
                body: { role, experience, interview_type, resume_text }
            }),
        submit: (role, experience, interview_type, answers) => 
            request('/interview/submit', {
                method: 'POST',
                body: { role, experience, interview_type, answers }
            })
    },
    dashboard: {
        summary: () => request('/dashboard/summary', { method: 'GET' }),
        history: () => request('/dashboard/history', { method: 'GET' })
    }
};

window.API = API;
