// App State Manager for InterviewForge SPA

document.addEventListener("DOMContentLoaded", () => {
    // ----------------------------------------------------
    // 1. STATE & ROUTING
    // ----------------------------------------------------
    const STATE = {
        user: null,
        activeView: "home",
        interview: {
            role: "",
            experience: "",
            interview_type: "",
            questions: [],
            answers: [], // Array of strings matching index of questions
            currentIdx: 0,
            resumeText: ""
        }
    };

    // DOM Elements
    const views = {
        home: document.getElementById("view-home"),
        auth: document.getElementById("view-auth"),
        setup: document.getElementById("view-setup"),
        session: document.getElementById("view-session"),
        loading: document.getElementById("view-loading"),
        report: document.getElementById("view-report"),
        dashboard: document.getElementById("view-dashboard")
    };

    const navLinks = {
        dashboard: document.getElementById("nav-dashboard-link"),
        auth: document.getElementById("nav-auth-btn"),
        logout: document.getElementById("nav-logout-btn"),
        username: document.getElementById("nav-username-display")
    };

    // View Switcher
    function showView(viewId) {
        // Redirect if already logged in and trying to access auth
        if (STATE.user && viewId === "auth") {
            showView("dashboard");
            return;
        }
        // Redirect to auth if trying to access dashboard while logged out
        if (!STATE.user && viewId === "dashboard") {
            showView("auth");
            return;
        }

        Object.keys(views).forEach(key => {
            if (views[key]) {
                if (key === viewId) {
                    views[key].classList.add("active");
                } else {
                    views[key].classList.remove("active");
                }
            }
        });
        STATE.activeView = viewId;
        window.scrollTo({ top: 0, behavior: 'smooth' });
        
        // Trigger specific view updates
        if (viewId === "dashboard") {
            loadDashboard();
        }
    }

    // Toast Notification helper
    function showToast(message, type = "success") {
        const toast = document.createElement("div");
        toast.className = `toast toast-${type} glass`;
        toast.innerHTML = `
            <span>${type === 'success' ? '✔' : '✕'}</span>
            <div>${message}</div>
        `;
        document.body.appendChild(toast);
        
        // Reflow for transition
        setTimeout(() => toast.classList.add("show"), 10);
        
        setTimeout(() => {
            toast.classList.remove("show");
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    // Helper to format error messages safely
    function getErrorMessage(err) {
        if (!err) return "An unknown error occurred.";
        let message = err.message || err;
        if (typeof message === 'object') {
            try {
                message = JSON.stringify(message);
            } catch (e) {
                message = String(message);
            }
        }
        if (message === "[object Object]" && err.detail) {
            if (typeof err.detail === 'string') {
                return err.detail;
            } else if (Array.isArray(err.detail)) {
                return err.detail.map(x => x.msg || JSON.stringify(x)).join(', ');
            } else {
                return JSON.stringify(err.detail);
            }
        }
        return String(message);
    }

    // Update Nav Bar state
    function updateNavbar() {
        const homeCtaGuest = document.getElementById("home-cta-guest");
        const homeCtaUser = document.getElementById("home-cta-user");
        if (STATE.user) {
            if (navLinks.dashboard) navLinks.dashboard.style.display = "inline-block";
            if (navLinks.username) {
                navLinks.username.style.display = "inline-flex";
                navLinks.username.title = STATE.user.username;
            }
            if (navLinks.auth) navLinks.auth.style.display = "none";
            if (navLinks.logout) navLinks.logout.style.display = "inline-flex";
            if (homeCtaGuest) homeCtaGuest.style.display = "none";
            if (homeCtaUser) homeCtaUser.style.display = "inline-flex";
        } else {
            if (navLinks.dashboard) navLinks.dashboard.style.display = "none";
            if (navLinks.username) {
                navLinks.username.style.display = "none";
                navLinks.username.title = "";
            }
            if (navLinks.auth) navLinks.auth.style.display = "inline-flex";
            if (navLinks.logout) navLinks.logout.style.display = "none";
            if (homeCtaGuest) homeCtaGuest.style.display = "inline-flex";
            if (homeCtaUser) homeCtaUser.style.display = "none";
        }
    }

    // Check auth on boot
    async function checkAuth() {
        try {
            const data = await API.auth.me();
            if (data.authenticated) {
                STATE.user = data.user;
            } else {
                STATE.user = null;
            }
            updateNavbar();
        } catch (e) {
            STATE.user = null;
            updateNavbar();
        }
    }

    // ----------------------------------------------------
    // 2. AUTHENTICATION LOGIC
    // ----------------------------------------------------
    const loginForm = document.getElementById("login-form");
    const registerForm = document.getElementById("register-form");
    const authTabLogin = document.getElementById("auth-tab-login");
    const authTabRegister = document.getElementById("auth-tab-register");

    // Toggle login/register tabs
    if (authTabLogin && authTabRegister) {
        authTabLogin.addEventListener("click", () => {
            authTabLogin.classList.add("active");
            authTabRegister.classList.remove("active");
            loginForm.style.display = "block";
            registerForm.style.display = "none";
        });

        authTabRegister.addEventListener("click", () => {
            authTabRegister.classList.add("active");
            authTabLogin.classList.remove("active");
            registerForm.style.display = "block";
            loginForm.style.display = "none";
        });
    }

    // Submit Register
    if (registerForm) {
        registerForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const username = document.getElementById("reg-username").value.trim();
            const email = document.getElementById("reg-email").value.trim();
            const password = document.getElementById("reg-password").value;
            const errorEl = document.getElementById("reg-error");

            errorEl.style.display = "none";

            try {
                await API.auth.register(username, email, password);
                showToast("Account created successfully! Please log in.");
                authTabLogin.click(); // switch to login tab
            } catch (err) {
                errorEl.textContent = getErrorMessage(err);
                errorEl.style.display = "block";
            }
        });
    }

    // Submit Login
    if (loginForm) {
        loginForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const email = document.getElementById("login-email").value.trim();
            const password = document.getElementById("login-password").value;
            const errorEl = document.getElementById("login-error");

            errorEl.style.display = "none";

            try {
                const data = await API.auth.login(email, password);
                STATE.user = data.user;
                updateNavbar();
                showToast(`Welcome back, ${data.user.username}!`);
                showView("dashboard");
            } catch (err) {
                errorEl.textContent = getErrorMessage(err);
                errorEl.style.display = "block";
            }
        });
    }

    // Logout confirmation modal DOM elements
    const logoutConfirmModal = document.getElementById("logout-confirm-modal");
    const logoutCancelBtn = document.getElementById("logout-cancel-btn");
    const logoutConfirmBtn = document.getElementById("logout-confirm-btn");

    // Profile modal DOM elements
    const profileModal = document.getElementById("profile-modal");
    const profileEmail = document.getElementById("profile-email");
    const profileUsername = document.getElementById("profile-username");
    const profileError = document.getElementById("profile-error");
    const profileSaveBtn = document.getElementById("profile-save-btn");
    const profileCancelBtn = document.getElementById("profile-cancel-btn");
    const profileModalClose = document.getElementById("profile-modal-close");

    // Show user profile modal on click
    if (navLinks.username) {
        navLinks.username.addEventListener("click", (e) => {
            e.preventDefault();
            if (STATE.user) {
                profileEmail.value = STATE.user.email || "";
                profileUsername.value = STATE.user.username || "";
                profileError.style.display = "none";
                profileError.textContent = "";
                profileModal.style.display = "flex";
            }
        });
    }

    // Close profile modal
    function closeProfileModal() {
        if (profileModal) profileModal.style.display = "none";
    }

    if (profileModalClose) profileModalClose.addEventListener("click", closeProfileModal);
    if (profileCancelBtn) profileCancelBtn.addEventListener("click", closeProfileModal);
    
    // Save Profile Changes
    if (profileSaveBtn) {
        profileSaveBtn.addEventListener("click", async () => {
            const newUsername = profileUsername.value.trim();
            if (!newUsername) {
                profileError.textContent = "Username cannot be empty.";
                profileError.style.display = "block";
                return;
            }
            
            // Check if username actually changed
            if (newUsername === STATE.user.username) {
                showToast("No changes detected.");
                closeProfileModal();
                return;
            }

            profileSaveBtn.disabled = true;
            profileSaveBtn.textContent = "Saving...";
            profileError.style.display = "none";

            try {
                const data = await API.auth.updateUsername(newUsername);
                STATE.user.username = data.username;
                updateNavbar();
                showToast("Username updated successfully!");
                closeProfileModal();
            } catch (err) {
                profileError.textContent = getErrorMessage(err);
                profileError.style.display = "block";
            } finally {
                profileSaveBtn.disabled = false;
                profileSaveBtn.textContent = "Save Changes";
            }
        });
    }

    // Logout trigger (Confirm dialog show)
    if (navLinks.logout) {
        navLinks.logout.addEventListener("click", (e) => {
            e.preventDefault();
            if (logoutConfirmModal) {
                logoutConfirmModal.style.display = "flex";
            }
        });
    }

    // Cancel Logout Modal
    if (logoutCancelBtn) {
        logoutCancelBtn.addEventListener("click", () => {
            if (logoutConfirmModal) {
                logoutConfirmModal.style.display = "none";
            }
        });
    }

    // Confirm Logout action
    if (logoutConfirmBtn) {
        logoutConfirmBtn.addEventListener("click", async () => {
            if (logoutConfirmModal) {
                logoutConfirmModal.style.display = "none";
            }
            try {
                await API.auth.logout();
                STATE.user = null;
                updateNavbar();
                showToast("Logged out successfully");
                showView("home");
            } catch (err) {
                showToast("Logout failed", "error");
            }
        });
    }

    // ----------------------------------------------------
    // 3. INTERVIEW SETUP LOGIC
    // ----------------------------------------------------
    const setupCloseBtn = document.getElementById("setup-close-btn");
    if (setupCloseBtn) {
        setupCloseBtn.addEventListener("click", () => {
            if (STATE.user) {
                showView("dashboard");
            } else {
                showView("home");
            }
        });
    }

    let selectedRole = "";
    let selectedExperience = "";
    let selectedType = "";

    // Selector click handlers
    document.querySelectorAll(".role-option").forEach(el => {
        el.addEventListener("click", () => {
            document.querySelectorAll(".role-option").forEach(x => x.classList.remove("selected"));
            el.classList.add("selected");
            selectedRole = el.dataset.role;
            
            // If custom role is clicked
            const customRoleContainer = document.getElementById("custom-role-container");
            if (selectedRole === "custom") {
                customRoleContainer.style.display = "block";
            } else {
                customRoleContainer.style.display = "none";
            }
        });
    });

    document.querySelectorAll(".experience-option").forEach(el => {
        el.addEventListener("click", () => {
            document.querySelectorAll(".experience-option").forEach(x => x.classList.remove("selected"));
            el.classList.add("selected");
            selectedExperience = el.dataset.exp;
        });
    });

    document.querySelectorAll(".type-option").forEach(el => {
        el.addEventListener("click", () => {
            document.querySelectorAll(".type-option").forEach(x => x.classList.remove("selected"));
            el.classList.add("selected");
            selectedType = el.dataset.type;
        });
    });

    // Resume drag/drop or text paste
    const resumeUploader = document.getElementById("resume-uploader");
    const resumeFileInput = document.getElementById("resume-file-input");
    const resumeTextarea = document.getElementById("resume-textarea");
    const resumeStatusText = document.getElementById("resume-status-text");

    if (resumeUploader) {
        resumeUploader.addEventListener("click", () => resumeFileInput.click());
        
        resumeFileInput.addEventListener("change", (e) => {
            const file = e.target.files[0];
            if (file) {
                if (file.type !== "text/plain") {
                    showToast("Only standard text (.txt) files are supported directly. For PDFs/Word docs, copy-paste resume text below.", "error");
                    resumeTextarea.style.display = "block";
                    return;
                }
                const reader = new FileReader();
                reader.onload = (evt) => {
                    STATE.interview.resumeText = evt.target.result;
                    resumeStatusText.textContent = `Attached: ${file.name}`;
                    resumeUploader.style.borderColor = "var(--primary)";
                    showToast("Resume text attached successfully!");
                };
                reader.readAsText(file);
            }
        });
    }

    // Toggle text area manually if they want to paste
    const btnTogglePaste = document.getElementById("btn-toggle-paste");
    if (btnTogglePaste) {
        btnTogglePaste.addEventListener("click", () => {
            if (resumeTextarea.style.display === "block") {
                resumeTextarea.style.display = "none";
                btnTogglePaste.textContent = "Or Paste Plain Text";
            } else {
                resumeTextarea.style.display = "block";
                btnTogglePaste.textContent = "Hide Paste Field";
                resumeTextarea.focus();
            }
        });
        
        resumeTextarea.addEventListener("input", () => {
            STATE.interview.resumeText = resumeTextarea.value.trim();
        });
    }

    // Start setup submission
    const startSetupBtn = document.getElementById("start-setup-btn");
    if (startSetupBtn) {
        startSetupBtn.addEventListener("click", async () => {
            let role = selectedRole;
            if (role === "custom") {
                role = document.getElementById("custom-role-input").value.trim();
            }

            if (!role) {
                showToast("Please select or enter an interview role.", "error");
                return;
            }
            if (!selectedExperience) {
                showToast("Please select your experience level.", "error");
                return;
            }
            if (!selectedType) {
                showToast("Please select interview type.", "error");
                return;
            }

            // Save details to state
            STATE.interview.role = role;
            STATE.interview.experience = selectedExperience;
            STATE.interview.interview_type = selectedType;
            
            // Read direct text area just in case they typed without focus triggers
            if (resumeTextarea.style.display === "block") {
                STATE.interview.resumeText = resumeTextarea.value.trim();
            }

            // Trigger AI Question Generation
            startSetupBtn.disabled = true;
            startSetupBtn.textContent = "Generating questions...";
            showToast("Connecting to AI Interviewer...");

            try {
                const data = await API.interview.setup(
                    STATE.interview.role,
                    STATE.interview.experience,
                    STATE.interview.interview_type,
                    STATE.interview.resumeText
                );

                STATE.interview.questions = data.questions;
                STATE.interview.answers = new Array(data.questions.length).fill("");
                STATE.interview.currentIdx = 0;

                showToast("Interview questions generated successfully!");
                launchInterviewSession();
            } catch (err) {
                showToast(getErrorMessage(err), "error");
            } finally {
                startSetupBtn.disabled = false;
                startSetupBtn.textContent = "Begin Interview";
            }
        });
    }

    // ----------------------------------------------------
    // 4. INTERVIEW FLOW LOGIC (SESSION)
    // ----------------------------------------------------
    const progressFill = document.getElementById("progress-fill");
    const progressText = document.getElementById("progress-text");
    const questionText = document.getElementById("question-text");
    const answerTextarea = document.getElementById("answer-textarea");
    const charCounter = document.getElementById("char-counter");
    const prevQuestionBtn = document.getElementById("prev-question-btn");
    const nextQuestionBtn = document.getElementById("next-question-btn");

    function launchInterviewSession() {
        showView("session");
        renderQuestion();
    }

    function renderQuestion() {
        const idx = STATE.interview.currentIdx;
        const total = STATE.interview.questions.length;
        
        // Progress bar
        const percent = ((idx + 1) / total) * 100;
        progressFill.style.width = `${percent}%`;
        progressText.textContent = `Question ${idx + 1} of ${total}`;

        // Question display
        questionText.textContent = STATE.interview.questions[idx];

        // Answer recovery
        answerTextarea.value = STATE.interview.answers[idx] || "";
        charCounter.textContent = `${answerTextarea.value.length} characters`;

        // Buttons configuration
        if (idx === 0) {
            prevQuestionBtn.style.display = "none";
        } else {
            prevQuestionBtn.style.display = "inline-flex";
        }

        if (idx === total - 1) {
            nextQuestionBtn.textContent = "Submit Interview";
            nextQuestionBtn.className = "btn btn-accent";
        } else {
            nextQuestionBtn.textContent = "Next Question";
            nextQuestionBtn.className = "btn btn-primary";
        }
    }

    // Answer text area character update
    if (answerTextarea) {
        answerTextarea.addEventListener("input", () => {
            charCounter.textContent = `${answerTextarea.value.length} characters`;
            STATE.interview.answers[STATE.interview.currentIdx] = answerTextarea.value;
        });
    }

    // Prev Button
    if (prevQuestionBtn) {
        prevQuestionBtn.addEventListener("click", () => {
            if (STATE.interview.currentIdx > 0) {
                // save current
                STATE.interview.answers[STATE.interview.currentIdx] = answerTextarea.value;
                STATE.interview.currentIdx--;
                renderQuestion();
            }
        });
    }

    // Next / Submit Button
    if (nextQuestionBtn) {
        nextQuestionBtn.addEventListener("click", async () => {
            // Save current answer
            const currentAnswer = answerTextarea.value.trim();
            if (!currentAnswer) {
                showToast("Please provide an answer before continuing.", "error");
                return;
            }
            STATE.interview.answers[STATE.interview.currentIdx] = currentAnswer;

            const idx = STATE.interview.currentIdx;
            const total = STATE.interview.questions.length;

            if (idx < total - 1) {
                STATE.interview.currentIdx++;
                renderQuestion();
            } else {
                // Submit batch for single-pass evaluation
                await evaluateInterview();
            }
        });
    }

    async function evaluateInterview() {
        // Compile answers list in payload format
        const submissions = STATE.interview.questions.map((q, index) => ({
            question: q,
            answer: STATE.interview.answers[index]
        }));

        showView("loading");
        showToast("AI is evaluating your answers...");

        try {
            const report = await API.interview.submit(
                STATE.interview.role,
                STATE.interview.experience,
                STATE.interview.interview_type,
                submissions
            );
            
            showToast("Evaluation completed!");
            renderReport(report);
        } catch (err) {
            showToast(getErrorMessage(err), "error");
            showView("session"); // return to session to retry
        }
    }

    // ----------------------------------------------------
    // 5. REPORT LOGIC
    // ----------------------------------------------------
    function renderReport(data) {
        showView("report");
        
        const r = data.report;
        const saved = data.saved;

        // Display Guest signup advertisement notice
        const guestNotice = document.getElementById("report-guest-notice");
        if (saved || STATE.user) {
            guestNotice.style.display = "none";
        } else {
            guestNotice.style.display = "flex";
        }

        // Circular progress score SVG drawing
        const scoreCircle = document.getElementById("report-score-fill");
        const scoreText = document.getElementById("report-score-text");
        
        scoreText.textContent = r.final_score;
        
        // Circumference: 2 * PI * r = 2 * 3.14159 * 56 = 351.8
        const circumference = 351.8;
        const offset = circumference - (circumference * r.final_score) / 100;
        
        // Reset and animate SVG progress stroke
        scoreCircle.style.strokeDashoffset = circumference;
        setTimeout(() => {
            scoreCircle.style.strokeDashoffset = offset;
        }, 150);

        // Core score metrics
        document.getElementById("report-technical-score").textContent = r.technical_score;
        document.getElementById("report-problemsolving-score").textContent = r.problem_solving_score;

        // Strengths & Weaknesses
        const strengthsList = document.getElementById("report-strengths");
        const weaknessesList = document.getElementById("report-weaknesses");
        
        strengthsList.innerHTML = r.strengths.map(s => `<li>${s}</li>`).join("");
        weaknessesList.innerHTML = r.weaknesses.map(w => `<li>${w}</li>`).join("");

        // Recommendations
        const recContainer = document.getElementById("report-recommendations");
        if (r.recommended_topics && r.recommended_topics.length > 0) {
            recContainer.innerHTML = r.recommended_topics.map(rec => `
                <div class="recommendation-item">
                    <span>${rec}</span>
                </div>
            `).join("");
        } else {
            recContainer.innerHTML = `<p class="no-data">No specific study topics recommended.</p>`;
        }
    }

    // Report View CTA redirection
    const reportCloseBtn = document.getElementById("report-close-btn");
    if (reportCloseBtn) {
        reportCloseBtn.addEventListener("click", () => {
            if (STATE.user) {
                showView("dashboard");
            } else {
                showView("home");
            }
        });
    }

    // ----------------------------------------------------
    // 6. DASHBOARD LOGIC
    // ----------------------------------------------------
    async function loadDashboard() {
        const metricsCount = document.getElementById("dash-total-count");
        const metricsAverage = document.getElementById("dash-avg-score");
        const metricsBest = document.getElementById("dash-best-score");
        const strongChips = document.getElementById("dash-strong-chips");
        const weakChips = document.getElementById("dash-weak-chips");
        const dashRecommendations = document.getElementById("dash-recommendations-list");
        const historyTimeline = document.getElementById("dash-history-timeline");

        // Clear view
        metricsCount.textContent = "-";
        metricsAverage.textContent = "-";
        metricsBest.textContent = "-";
        strongChips.innerHTML = "";
        weakChips.innerHTML = "";
        dashRecommendations.innerHTML = "";
        historyTimeline.innerHTML = `<div class="skeleton-text"></div><div class="skeleton-text"></div>`;

        try {
            const summary = await API.dashboard.summary();
            const history = await API.dashboard.history();

            // Set metrics
            metricsCount.textContent = summary.total_interviews;
            metricsAverage.textContent = `${summary.average_score}%`;
            metricsBest.textContent = `${summary.best_score}%`;

            // Strong Areas
            if (summary.strong_areas && summary.strong_areas.length > 0) {
                strongChips.innerHTML = summary.strong_areas.map(s => `<span class="chip chip-strong">${s}</span>`).join("");
            } else {
                strongChips.innerHTML = `<span class="no-data">No strong areas logged yet.</span>`;
            }

            // Weak Areas
            if (summary.weak_areas && summary.weak_areas.length > 0) {
                weakChips.innerHTML = summary.weak_areas.map(w => `<span class="chip chip-weak">${w}</span>`).join("");
            } else {
                weakChips.innerHTML = `<span class="no-data">No weak areas logged yet.</span>`;
            }

            // Recommendations
            if (summary.recommendations && summary.recommendations.length > 0) {
                dashRecommendations.innerHTML = summary.recommendations.map(r => `
                    <div class="recommendation-item">
                        <span>${r}</span>
                    </div>
                `).join("");
            } else {
                dashRecommendations.innerHTML = `<p class="no-data">No aggregated suggestions yet. Finish interviews to see recommendations.</p>`;
            }

            // Render History timeline
            if (history && history.length > 0) {
                historyTimeline.innerHTML = history.map(item => {
                    const parsedDate = new Date(item.completed_at).toLocaleDateString(undefined, {
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric'
                    });
                    
                    const passedClass = item.final_score >= 75 ? "passed-75" : "";

                    const strengthsHtml = item.report.strengths.map(s => `<li>${s}</li>`).join("");
                    const weaknessesHtml = item.report.weaknesses.map(w => `<li>${w}</li>`).join("");
                    const recHtml = item.report.recommended_topics.map(r => `<span class="chip chip-strong" style="font-size:0.75rem">${r}</span>`).join("");

                    return `
                        <div class="timeline-item ${passedClass}">
                            <div class="timeline-meta">
                                <span class="timeline-role">${item.role}</span>
                                <span class="timeline-score">${item.final_score}/100</span>
                            </div>
                            <div class="timeline-details">
                                <span>${item.interview_type}</span>
                                <span>•</span>
                                <span>${item.experience_level}</span>
                                <span>•</span>
                                <span>${parsedDate}</span>
                            </div>
                            <button class="timeline-item-btn" data-id="${item.session_id}">Expand Evaluation Details</button>
                            <div class="timeline-expandable-report" id="expand-${item.session_id}">
                                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:16px; margin-top:10px;">
                                    <div>
                                        <h5 style="color:var(--success); margin-bottom:6px;">Strengths</h5>
                                        <ul style="padding-left:16px; font-size:0.85rem; line-height:1.4;">${strengthsHtml || "None"}</ul>
                                    </div>
                                    <div>
                                        <h5 style="color:var(--danger); margin-bottom:6px;">Weaknesses</h5>
                                        <ul style="padding-left:16px; font-size:0.85rem; line-height:1.4;">${weaknessesHtml || "None"}</ul>
                                    </div>
                                </div>
                                <div style="margin-top:14px;">
                                    <h5 style="margin-bottom:6px; font-size:0.85rem;">Study Topics</h5>
                                    <div style="display:flex; flex-wrap:wrap; gap:6px;">${recHtml || "None"}</div>
                                </div>
                            </div>
                        </div>
                    `;
                }).join("");

                // Add toggle listeners
                document.querySelectorAll(".timeline-item-btn").forEach(btn => {
                    btn.addEventListener("click", () => {
                        const sId = btn.dataset.id;
                        const panel = document.getElementById(`expand-${sId}`);
                        if (panel.classList.contains("active")) {
                            panel.classList.remove("active");
                            btn.textContent = "Expand Evaluation Details";
                        } else {
                            panel.classList.add("active");
                            btn.textContent = "Hide Evaluation Details";
                        }
                    });
                });

            } else {
                historyTimeline.innerHTML = `<div class="no-data">No completed interviews yet. Click "Start Interview" to practice!</div>`;
            }

        } catch (err) {
            showToast("Failed to load dashboard metrics", "error");
            historyTimeline.innerHTML = `<div class="no-data" style="color:var(--danger)">Error loading metrics.</div>`;
        }
    }

    // ----------------------------------------------------
    // 7. GLOBAL BINDINGS & SPA ROUTER EVENTS
    // ----------------------------------------------------
    document.querySelectorAll(".lnk-goto-setup").forEach(el => {
        el.addEventListener("click", (e) => {
            e.preventDefault();
            showView("setup");
        });
    });

    document.querySelectorAll(".lnk-goto-home").forEach(el => {
        el.addEventListener("click", (e) => {
            e.preventDefault();
            showView("home");
        });
    });

    document.querySelectorAll(".lnk-goto-auth").forEach(el => {
        el.addEventListener("click", (e) => {
            e.preventDefault();
            showView("auth");
        });
    });

    document.querySelectorAll(".lnk-goto-dashboard").forEach(el => {
        el.addEventListener("click", (e) => {
            e.preventDefault();
            showView("dashboard");
        });
    });

    if (navLinks.dashboard) {
        navLinks.dashboard.addEventListener("click", (e) => {
            e.preventDefault();
            showView("dashboard");
        });
    }

    // Hamburger Menu Management
    function initMobileMenu() {
        const menuToggle = document.getElementById("menu-toggle");
        const navMenu = document.getElementById("nav-menu");

        if (menuToggle && navMenu) {
            menuToggle.addEventListener("click", (e) => {
                e.stopPropagation();
                menuToggle.classList.toggle("open");
                navMenu.classList.toggle("open");
            });

            // Close menu when clicking any link/button inside it
            navMenu.querySelectorAll("a, button, span").forEach(el => {
                el.addEventListener("click", () => {
                    menuToggle.classList.remove("open");
                    navMenu.classList.remove("open");
                });
            });

            // Close menu when clicking outside
            document.addEventListener("click", (e) => {
                if (navMenu.classList.contains("open")) {
                    if (!navMenu.contains(e.target) && !menuToggle.contains(e.target)) {
                        menuToggle.classList.remove("open");
                        navMenu.classList.remove("open");
                    }
                }
            });
        }
    }

    initMobileMenu();

    // Theme Management
    function initTheme() {
        const themeToggleBtn = document.getElementById("theme-toggle-btn");
        const savedTheme = localStorage.getItem("theme");
        
        // Use system preference as fallback
        const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
        const defaultTheme = prefersDark ? "dark" : "light";
        const currentTheme = savedTheme || defaultTheme;
        
        // Apply theme attribute to html element
        document.documentElement.setAttribute("data-theme", currentTheme);
        
        if (themeToggleBtn) {
            themeToggleBtn.addEventListener("click", () => {
                const activeTheme = document.documentElement.getAttribute("data-theme");
                const newTheme = activeTheme === "dark" ? "light" : "dark";
                
                document.documentElement.setAttribute("data-theme", newTheme);
                localStorage.setItem("theme", newTheme);
                showToast(`Switched to ${newTheme} mode!`, "success");
            });
        }
    }

    // Initial check
    initTheme();
    
    // FAQ Accordion Management
    function initFaq() {
        const faqQuestions = document.querySelectorAll(".faq-question");
        faqQuestions.forEach(question => {
            question.addEventListener("click", () => {
                const item = question.closest(".faq-item");
                const answer = item.querySelector(".faq-answer");
                const isActive = item.classList.contains("active");

                // Close all other FAQ items
                document.querySelectorAll(".faq-item").forEach(otherItem => {
                    if (otherItem !== item) {
                        otherItem.classList.remove("active");
                        otherItem.querySelector(".faq-answer").style.maxHeight = null;
                    }
                });

                // Toggle current FAQ item
                if (isActive) {
                    item.classList.remove("active");
                    answer.style.maxHeight = null;
                } else {
                    item.classList.add("active");
                    answer.style.maxHeight = answer.scrollHeight + "px";
                }
            });
        });
    }
    
    initFaq();

    checkAuth().then(() => {
        showView("home");
    });
});
