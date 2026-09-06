// =====================================================
// PLANORA AI - MAIN JAVASCRIPT
// =====================================================

document.addEventListener("DOMContentLoaded", () => {
    loadPlans();
    setMinimumExamDate();
    loadTheme();
    setupAIInput();
});


// =====================================================
// NAVIGATION
// =====================================================

function showSection(sectionId, clickedButton = null) {

    document.querySelectorAll(".content-section").forEach(section => {
        section.classList.remove("active-section");
    });

    const section = document.getElementById(sectionId);

    if (section) {
        section.classList.add("active-section");
    }

    document.querySelectorAll(".nav-item").forEach(button => {
        button.classList.remove("active");
    });

    if (clickedButton) {
        clickedButton.classList.add("active");
    }
}


function openPlanner() {

    showSection("plannerSection");

    document.querySelectorAll(".nav-item").forEach(button => {
        button.classList.remove("active");
    });
}


// =====================================================
// EXAM DATE
// =====================================================

function setMinimumExamDate() {

    const examDate = document.getElementById("examDate");

    if (!examDate) return;

    const today = new Date();

    const year = today.getFullYear();

    const month = String(
        today.getMonth() + 1
    ).padStart(2, "0");

    const day = String(
        today.getDate()
    ).padStart(2, "0");

    examDate.min = `${year}-${month}-${day}`;
}


// =====================================================
// CREATE STUDY PLAN
// =====================================================

const plannerForm = document.getElementById("plannerForm");

if (plannerForm) {

    plannerForm.addEventListener(
        "submit",
        async function(event) {

            event.preventDefault();

            const subjectsText =
                document.getElementById("subjects").value;

            const examDate =
                document.getElementById("examDate").value;

            const studyHours =
                Number(
                    document.getElementById("studyHours").value
                );

            const goal =
                document.getElementById("goal").value;

            const notes =
                document.getElementById("notes").value;

            const subjects =
                subjectsText
                    .split(",")
                    .map(subject => subject.trim())
                    .filter(subject => subject);

            if (subjects.length === 0) {

                alert("Please enter at least one subject.");

                return;
            }

            const resultBox =
                document.getElementById("generatedPlan");

            if (resultBox) {

                resultBox.classList.remove("hidden");

                resultBox.innerHTML = `
                    <h3>✨ Your Study Plan</h3>
                    <p>
                        Creating your personalized schedule...
                    </p>
                `;
            }

            const plan =
                createPlan(
                    subjects,
                    examDate,
                    studyHours,
                    goal,
                    notes
                );

            if (resultBox) {

                resultBox.innerHTML =
                    renderGeneratedPlan(plan);
            }

            try {

                const response =
                    await fetch(
                        "/api/save-plan",
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body:
                                JSON.stringify(plan)
                        }
                    );

                const result =
                    await response.json();

                if (result.success && resultBox) {

                    resultBox.innerHTML += `
                        <div class="success-message">
                            ✅ Study plan saved successfully!
                        </div>
                    `;

                    loadPlans();
                }

            } catch (error) {

                console.error(
                    "Save plan error:",
                    error
                );
            }
        }
    );
}


// =====================================================
// PLAN GENERATOR
// =====================================================

function createPlan(
    subjects,
    examDate,
    studyHours,
    goal,
    notes
) {

    const days =
        calculateDaysUntilExam(examDate);

    const availableDays =
        Math.max(days, 1);

    const schedule = [];

    subjects.forEach((subject, index) => {

        const dayNumber =
            (index %
                Math.min(
                    availableDays,
                    7
                )
            ) + 1;

        const date =
            new Date();

        date.setDate(
            date.getDate()
            + dayNumber
            - 1
        );

        const dateText =
            date.toLocaleDateString(
                "en-IN",
                {
                    day: "2-digit",
                    month: "short"
                }
            );

        schedule.push({

            day:
                `Day ${dayNumber}`,

            date:
                dateText,

            subject:
                subject,

            hours:
                Math.max(
                    1,
                    Math.round(
                        studyHours /
                        Math.min(
                            subjects.length,
                            studyHours || 1
                        )
                    )
                ),

            task:
                goal === "Revision"
                    ?
                    `Revise ${subject} and practice important questions`
                    :
                    `Study ${subject} concepts and make short notes`
        });

    });

    return {

        subjects:
            subjects,

        exam_date:
            examDate,

        study_hours:
            studyHours,

        goal:
            goal,

        notes:
            notes,

        days_remaining:
            availableDays,

        schedule:
            schedule
    };
}


// =====================================================
// DAYS CALCULATION
// =====================================================

function calculateDaysUntilExam(examDate) {

    if (!examDate) {
        return 1;
    }

    const today =
        new Date();

    const exam =
        new Date(
            examDate + "T23:59:59"
        );

    const difference =
        exam - today;

    return Math.max(
        1,
        Math.ceil(
            difference /
            (1000 * 60 * 60 * 24)
        )
    );
}


// =====================================================
// RENDER GENERATED PLAN
// =====================================================

function renderGeneratedPlan(plan) {

    let html = `

        <h3>
            ✨ Personalized Study Schedule
        </h3>

        <p>
            📅 Exam:
            <strong>
                ${escapeHTML(plan.exam_date)}
            </strong>
        </p>

        <p>
            ⏰ Daily study:
            <strong>
                ${plan.study_hours} hours
            </strong>
        </p>

        <p>
            🎯 Goal:
            <strong>
                ${escapeHTML(plan.goal)}
            </strong>
        </p>
    `;

    plan.schedule.forEach(item => {

        html += `

            <div class="plan-item">

                <strong>
                    ${escapeHTML(item.day)}
                    —
                    ${escapeHTML(item.subject)}
                </strong>

                <span>
                    📅 ${escapeHTML(item.date)}
                    &nbsp; • &nbsp;
                    ⏰ ${item.hours} hour(s)
                </span>

                <p>
                    ${escapeHTML(item.task)}
                </p>

            </div>
        `;
    });

    return html;
}


// =====================================================
// LOAD PLANS
// =====================================================

async function loadPlans() {

    try {

        const response =
            await fetch("/api/plans");

        if (!response.ok) {
            return;
        }

        const result =
            await response.json();

        if (!result.success) {
            return;
        }

        renderSavedPlans(result.plans);

        updateStats(result.plans);

    } catch (error) {

        console.error(
            "Could not load plans:",
            error
        );
    }
}


// =====================================================
// RENDER SAVED PLANS
// =====================================================

function renderSavedPlans(plans) {

    const container =
        document.getElementById(
            "plansContainer"
        );

    if (!container) return;

    if (!plans || plans.length === 0) {

        container.innerHTML = `

            <div class="empty-state">

                <div>📭</div>

                <h3>
                    No study plans yet
                </h3>

                <p>
                    Create your first study plan
                    to get started.
                </p>

                <button
                    class="primary-btn"
                    onclick="openPlanner()"
                >
                    Create Plan
                </button>

            </div>
        `;

        return;
    }

    container.innerHTML = "";

    [...plans]
        .reverse()
        .forEach(plan => {

            const card =
                document.createElement("div");

            card.className =
                "saved-plan";

            const subjects =
                Array.isArray(
                    plan.subjects
                )
                    ?
                    plan.subjects
                    :
                    [];

            card.innerHTML = `

                <div class="saved-plan-header">

                    <div>

                        <h3>
                            📚
                            ${escapeHTML(
                                plan.goal ||
                                "Study Plan"
                            )}
                        </h3>

                        <p>
                            Exam date:
                            ${escapeHTML(
                                plan.exam_date ||
                                "-"
                            )}
                        </p>

                    </div>

                    <button
                        class="plan-delete"
                        onclick="deletePlan('${escapeHTML(plan.id)}')"
                    >
                        🗑️
                    </button>

                </div>

                <div class="plan-tags">

                    ${subjects.map(
                        subject => `

                            <span class="plan-tag">
                                ${escapeHTML(subject)}
                            </span>
                        `
                    ).join("")}

                </div>

                <p>
                    ⏰
                    ${plan.study_hours || 0}
                    hours/day

                    &nbsp; • &nbsp;

                    📅
                    ${plan.days_remaining || 1}
                    day(s)
                </p>

            `;

            container.appendChild(card);
        });
}


// =====================================================
// DELETE PLAN
// =====================================================

async function deletePlan(id) {

    if (
        !confirm(
            "Delete this study plan?"
        )
    ) {
        return;
    }

    try {

        const response =
            await fetch(
                `/api/delete-plan/${encodeURIComponent(id)}`,
                {
                    method: "DELETE"
                }
            );

        const result =
            await response.json();

        if (result.success) {

            loadPlans();

        } else {

            alert(
                result.message ||
                "Could not delete plan."
            );
        }

    } catch (error) {

        console.error(error);

        alert(
            "Something went wrong."
        );
    }
}


// =====================================================
// CLEAR ALL PLANS
// =====================================================

async function clearAllPlans() {

    if (
        !confirm(
            "Are you sure you want to delete all study plans?"
        )
    ) {
        return;
    }

    try {

        const response =
            await fetch(
                "/api/clear-plans",
                {
                    method: "DELETE"
                }
            );

        const result =
            await response.json();

        if (result.success) {

            loadPlans();

            alert(
                "All study plans have been cleared."
            );
        }

    } catch (error) {

        console.error(error);

        alert(
            "Something went wrong."
        );
    }
}


// =====================================================
// STATISTICS
// =====================================================

function updateStats(plans) {

    const totalPlans =
        document.getElementById(
            "totalPlans"
        );

    const totalSubjects =
        document.getElementById(
            "totalSubjects"
        );

    const totalHours =
        document.getElementById(
            "totalHours"
        );

    if (!totalPlans) {
        return;
    }

    totalPlans.textContent =
        plans.length;

    const subjects =
        new Set();

    let hours = 0;

    plans.forEach(plan => {

        if (
            Array.isArray(
                plan.subjects
            )
        ) {

            plan.subjects.forEach(
                subject => {

                    subjects.add(
                        subject
                    );
                }
            );
        }

        hours += Number(
            plan.study_hours || 0
        );
    });

    if (totalSubjects) {

        totalSubjects.textContent =
            subjects.size;
    }

    if (totalHours) {

        totalHours.textContent =
            hours;
    }
}


// =====================================================
// 🤖 REAL GEMINI AI ASSISTANT
// =====================================================

let aiSending = false;


async function askAI() {

    const input =
        document.getElementById(
            "aiQuestion"
        );

    const responseBox =
        document.getElementById(
            "aiResponse"
        );

    if (!input || !responseBox) {
        return;
    }

    const question =
        input.value.trim();

    if (!question) {
        return;
    }

    // Prevent double sending
    if (aiSending) {
        return;
    }

    aiSending = true;


    // =================================================
    // DISABLE SEND BUTTON
    // =================================================

    const sendButton =
        document.querySelector(
            ".ai-input button"
        );

    if (sendButton) {

        sendButton.disabled = true;

        sendButton.dataset.originalText =
            sendButton.textContent;

        sendButton.textContent =
            "⏳ Sending...";
    }


    // =================================================
    // USER MESSAGE
    // =================================================

    responseBox.innerHTML += `

        <div class="plan-item">

            <strong>
                👤 You
            </strong>

            <p>
                ${escapeHTML(question)}
            </p>

        </div>
    `;


    // Clear input
    input.value = "";


    // =================================================
    // THINKING MESSAGE
    // =================================================

    const thinkingId =
        "thinking-" +
        Date.now();

    responseBox.innerHTML += `

        <div
            class="plan-item"
            id="${thinkingId}"
        >

            <strong>
                🤖 Planora AI
            </strong>

            <p>
                ⏳ Thinking...
            </p>

        </div>
    `;


    // Scroll
    responseBox.scrollTop =
        responseBox.scrollHeight;


    try {

        // =================================================
        // CALL FLASK
        // =================================================

        const result =
            await fetch(
                "/chat",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify({
                            message:
                                question
                        })
                }
            );


        const data =
            await result.json();


        // =================================================
        // REMOVE THINKING
        // =================================================

        const thinking =
            document.getElementById(
                thinkingId
            );

        if (thinking) {
            thinking.remove();
        }


        // =================================================
        // ERROR
        // =================================================

        if (!data.success) {

            responseBox.innerHTML += `

                <div class="plan-item">

                    <strong>
                        🤖 Planora AI
                    </strong>

                    <p>
                        ❌
                        ${escapeHTML(
                            data.message ||
                            "Something went wrong."
                        )}
                    </p>

                </div>
            `;

            return;
        }


        // =================================================
        // AI RESPONSE
        // =================================================

        responseBox.innerHTML += `

            <div class="plan-item">

                <strong>
                    🤖 Planora AI
                </strong>

                <div class="ai-message">

                    ${formatAIResponse(
                        data.response
                    )}

                </div>

            </div>
        `;


        responseBox.scrollTop =
            responseBox.scrollHeight;


    } catch (error) {

        console.error(
            "AI Error:",
            error
        );


        const thinking =
            document.getElementById(
                thinkingId
            );

        if (thinking) {
            thinking.remove();
        }


        responseBox.innerHTML += `

            <div class="plan-item">

                <strong>
                    🤖 Planora AI
                </strong>

                <p>
                    ❌ Unable to connect
                    to Planora AI.
                    Please try again.
                </p>

            </div>
        `;

    } finally {

        // =================================================
        // ENABLE SEND BUTTON AGAIN
        // =================================================

        aiSending = false;

        if (sendButton) {

            sendButton.disabled = false;

            sendButton.textContent =
                sendButton.dataset.originalText ||
                "Send →";
        }

        input.focus();
    }
}


// =====================================================
// ENTER KEY → SEND
// =====================================================

function setupAIInput() {

    const input =
        document.getElementById(
            "aiQuestion"
        );

    if (!input) {
        return;
    }


    input.addEventListener(
        "keydown",
        function(event) {

            // Enter = Send
            // Shift + Enter = New line

            if (
                event.key === "Enter" &&
                !event.shiftKey
            ) {

                event.preventDefault();

                askAI();
            }
        }
    );
}


// =====================================================
// FORMAT AI RESPONSE
// =====================================================

function formatAIResponse(text) {

    if (!text) {
        return "";
    }

    let formatted =
        escapeHTML(text);


    // =================================================
    // HEADINGS
    // =================================================

    formatted =
        formatted.replace(
            /^###\s+(.*?)$/gm,
            "<h4>$1</h4>"
        );

    formatted =
        formatted.replace(
            /^##\s+(.*?)$/gm,
            "<h3>$1</h3>"
        );

    formatted =
        formatted.replace(
            /^#\s+(.*?)$/gm,
            "<h3>$1</h3>"
        );


    // =================================================
    // BOLD
    // =================================================

    formatted =
        formatted.replace(
            /\*\*(.*?)\*\*/g,
            "<strong>$1</strong>"
        );


    // =================================================
    // ITALIC
    // =================================================

    formatted =
        formatted.replace(
            /\*(.*?)\*/g,
            "<em>$1</em>"
        );


    // =================================================
    // CODE
    // =================================================

    formatted =
        formatted.replace(
            /`([^`]+)`/g,
            "<code>$1</code>"
        );


    // =================================================
    // BULLET POINTS
    // =================================================

    formatted =
        formatted.replace(
            /^[\t ]*[-•]\s+(.*?)$/gm,
            "• $1"
        );


    // =================================================
    // REMOVE MARKDOWN HORIZONTAL LINE
    // =================================================

    formatted =
        formatted.replace(
            /^\\?---+$/gm,
            ""
        );


    // =================================================
    // CLEAN EXTRA ESCAPES
    // =================================================

    formatted =
        formatted.replace(
            /\\---/g,
            ""
        );


    // =================================================
    // LINE BREAKS
    // =================================================

    formatted =
        formatted.replace(
            /\n/g,
            "<br>"
        );


    return formatted;
}


// =====================================================
// DARK MODE
// =====================================================

function toggleTheme() {

    document.body.classList.toggle(
        "dark"
    );

    const dark =
        document.body.classList.contains(
            "dark"
        );

    localStorage.setItem(
        "planoraTheme",
        dark
            ? "dark"
            : "light"
    );
}


function loadTheme() {

    const theme =
        localStorage.getItem(
            "planoraTheme"
        );

    if (theme === "dark") {

        document.body.classList.add(
            "dark"
        );
    }
}


// =====================================================
// SECURITY
// =====================================================

function escapeHTML(value) {

    return String(value)

        .replace(
            /&/g,
            "&amp;"
        )

        .replace(
            /</g,
            "&lt;"
        )

        .replace(
            />/g,
            "&gt;"
        )

        .replace(
            /"/g,
            "&quot;"
        )

        .replace(
            /'/g,
            "&#039;"
        );
}