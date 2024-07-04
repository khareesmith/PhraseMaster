// Global variables
let currentChallengeId = '';
let currentCategory = '';
let currentOriginalPrompt = '';
let hasScored = false;
let serverClientTimeDiff = 0;
let characterLimit = 150; // Default limit
let isPremiumUser = false; // Flag for premium users

// DOM elements object
const elements = {
    categoryButtons: document.querySelectorAll('.category-buttons button'),
    challengeDisplay: document.getElementById('challenge'),
    promptDisplay: document.getElementById('prompt'),
    phraseInput: document.getElementById('phraseInput'),
    submitPhraseButton: document.getElementById('submit_phrase_button'),
    resubmitPhraseButton: document.getElementById('resubmit_phrase_button'),
    feedbackDisplay: document.getElementById('feedback'),
    submissionForm: document.getElementById('submissionForm'),
    clearFeedbackButton: document.getElementById('clear_feedback_button'),
    scoreFirstToggle: document.getElementById('scoreFirstToggle'),
    timer: document.getElementById('timer'),
    datetime: document.getElementById('datetime'),
    serverTime: document.getElementById('server-time'),
    currentCount: document.getElementById('currentCount'),
    maxCount: document.getElementById('maxCount')
};

// Initialize the application
function init() {
    setupClearFeedbackButton();
    setupEventListeners();
    setDateDisplay();
    initializeTimer();
}

// Set up event listeners
function setupEventListeners() {
    elements.categoryButtons.forEach(button => {
        button.addEventListener('click', () => fetchChallenge(button.id));
    });
    elements.submitPhraseButton.addEventListener('click', submitPhrase);
    elements.clearFeedbackButton.addEventListener('click', resetUI);
    elements.scoreFirstToggle.addEventListener('change', updateButtonText);
    elements.phraseInput.addEventListener('input', updateCharCount);
}

// Function to update character count
function updateCharCount() {
    const count = elements.phraseInput.value.length;
    elements.currentCount.textContent = count;
    
    if (!isPremiumUser && count > characterLimit) {
        elements.phraseInput.value = elements.phraseInput.value.slice(0, characterLimit);
        elements.currentCount.textContent = characterLimit;
    }
    
    // Disable submit button if over limit or empty
    elements.submitPhraseButton.disabled = count === 0 || (!isPremiumUser && count > characterLimit);
}

// Set initial max count
maxCount.textContent = characterLimit;

// Function to set character limit (can be called to update limit)
function setCharacterLimit(limit) {
    characterLimit = limit;
    maxCount.textContent = limit;
    updateCharCount();
}

// Function to toggle premium status
function togglePremiumStatus(isPremium) {
    isPremiumUser = isPremium;
    if (isPremium) {
        maxCount.textContent = 'Unlimited';
    } else {
        maxCount.textContent = characterLimit;
    }
    updateCharCount();
}

// Update submit button text based on scoring toggle
function updateButtonText() {
    elements.submitPhraseButton.textContent = (elements.scoreFirstToggle.checked && !hasScored) ? 'Score Phrase' : 'Submit Phrase';
}

// Set up clear feedback button
function setupClearFeedbackButton() {
    elements.clearFeedbackButton.textContent = 'Continue';
    elements.clearFeedbackButton.classList.add('btn', 'btn-secondary', 'mt-3', 'm-0', 'm-auto');
    elements.clearFeedbackButton.style.display = 'none';
    elements.feedbackDisplay.parentNode.insertBefore(elements.clearFeedbackButton, elements.feedbackDisplay.nextSibling);
}

// Set the current date display
function setDateDisplay() {
    if (elements.datetime) {
        elements.datetime.innerHTML = new Date().toLocaleDateString();
    }
}

// Initialize the timer
function initializeTimer() {
    if (elements.serverTime) {
        const serverTime = elements.serverTime.dataset.time;
        syncTime(serverTime);
        updateTimer();
    }
}

// Synchronize client time with server time
function syncTime(serverTime) {
    const serverDate = new Date(serverTime);
    const clientDate = new Date();
    serverClientTimeDiff = serverDate - clientDate;
}

// Update the countdown timer
function updateTimer() {
    const now = new Date(new Date().getTime() + serverClientTimeDiff);
    const et = new Date(now.toLocaleString("en-US", {timeZone: "America/New_York"}));
    const midnight = new Date(et.getFullYear(), et.getMonth(), et.getDate() + 1);

    const timeLeft = midnight - et;
    const hours = Math.floor(timeLeft / (1000 * 60 * 60));
    const minutes = Math.floor((timeLeft % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((timeLeft % (1000 * 60)) / 1000);

    if (elements.timer) {
        elements.timer.innerHTML = `Next update: ${hours}h ${minutes}m ${seconds}s`;
    }

    setTimeout(updateTimer, 1000);
}

// Fetch a new challenge from the server
async function fetchChallenge(category) {
    if (!validateRequiredElements()) return;

    clearFeedback();
    resetUI();
    elements.promptDisplay.textContent = 'Loading...';
    elements.challengeDisplay.style.display = 'block';

    try {
        const response = await fetch(`/api/generate_challenge/${category}`);
        const data = await response.json();
        currentChallengeId = data.challenge_id;
        currentOriginalPrompt = data.challenge;
        currentCategory = data.category;
        updateChallenge(data);
    } catch (error) {
        console.error('Error:', error);
        elements.promptDisplay.textContent = 'Failed to load challenge. Please try again.';
    }
}

// Validate that all required DOM elements are present
function validateRequiredElements() {
    const requiredElements = [elements.feedbackDisplay, elements.phraseInput, elements.challengeDisplay, elements.submissionForm, elements.promptDisplay];
    if (requiredElements.some(el => !el)) {
        console.error('Required elements are missing in the DOM.');
        return false;
    }
    return true;
}

// Reset the UI to its initial state
function resetUI() {
    elements.phraseInput.value = '';
    elements.scoreFirstToggle.checked = false;
    elements.scoreFirstToggle.disabled = false;
    hasScored = false;
    updateButtonText();
}

// Update the challenge display
function updateChallenge(data) {
    fadeTransition(elements.promptDisplay, data.challenge);
    elements.submissionForm.style.display = 'block';
    updateButtonText();
    checkPreviousScore();
}
// Check if the challenge has been previously scored
function checkPreviousScore() {
    fetch(`/api/check_previous_score/${currentChallengeId}`)
        .then(response => response.json())
        .then(data => {
            if (data.previously_scored) {
                elements.scoreFirstToggle.checked = true;
                elements.scoreFirstToggle.disabled = true;
                hasScored = true;
                updateButtonText();
            }
        })
        .catch(error => console.error('Error checking previous score:', error));
}

// Apply a fade transition effect to an element
function fadeTransition(element, newText) {
    element.style.opacity = '0';
    setTimeout(() => {
        element.textContent = newText;
        element.style.opacity = '1';
    }, 300);
}

// Submit a phrase to the server
async function submitPhrase() {
    const userPhrase = elements.phraseInput.value.trim();
    const scoreFirst = elements.scoreFirstToggle.checked;

    if (!userPhrase) {
        displayFeedback('Please enter a phrase before submitting.', 'error');
        return;
    }

    displayFeedback('Submitting...', '');

    try {
        const response = await sendPhraseToServer(userPhrase, scoreFirst);
        const data = await response.json();

        if (!response.ok) throw new Error(data.error);

        if (data.message === 'Phrase scored') {
            displayFeedback(formatFeedback(data.feedback), 'info');
            hasScored = true;
            elements.scoreFirstToggle.disabled = true;
            updateButtonText();
        } else if (data.message === 'Submission successful!') {
            displayFeedback("Phrase submitted successfully!", 'success');
            setTimeout(resetUI, 2000);
        }
    } catch (error) {
        console.error('Error submitting phrase:', error);
        displayFeedback(`Error: ${error.message}`, 'error');
    }
}

// Display feedback to the user
function displayFeedback(message, type) {
    elements.feedbackDisplay.innerHTML = message;
    elements.feedbackDisplay.style.display = 'block';

    // Remove all existing alert classes
    elements.feedbackDisplay.classList.remove('alert-success', 'alert-danger', 'alert-warning', 'alert-info');

    // Add the appropriate alert class based on the type
    switch(type) {
        case 'success':
            elements.feedbackDisplay.classList.add('alert-success');
            break;
        case 'error':
            elements.feedbackDisplay.classList.add('alert-danger');
            break;
        case 'warning':
            elements.feedbackDisplay.classList.add('alert-warning');
            break;
        case 'info':
        default:
            elements.feedbackDisplay.classList.add('alert-info');
            break;
    }
}

// Clear the feedback display
function clearFeedback() {
    elements.feedbackDisplay.textContent = '';
    elements.feedbackDisplay.style.display = 'none';
}

// Send the phrase to the server
async function sendPhraseToServer(userPhrase, scoreFirst) {
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    return fetch('/api/submit_phrase', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            user_id: sessionStorage.getItem('user_id'),
            username: sessionStorage.getItem('username'),
            user_phrase: userPhrase,
            challenge_id: currentChallengeId,
            original_prompt: currentOriginalPrompt,
            category: currentCategory,
            score_first: scoreFirst
        })
    });
}

function formatFeedback(feedback) {
    const parts = feedback.split('\n\n').reduce((acc, part) => {
        const [key, ...value] = part.split(':');
        acc[key.trim().toLowerCase()] = value.join(':').trim();
        return acc;
    }, {});

    return `
        <strong>Evaluation By GPT</strong>
        <p class='mt-2 mb-0'><strong>Strengths:</strong></p>
        <ul class='list-group list-group-flush'>${formatList(parts.strengths)}</ul>
        <p class='mt-4 mb-0'><strong>Weaknesses:</strong></p>
        <ul class='list-group list-group-flush'>${formatList(parts.weaknesses)}</ul>
        <p class='mt-3'><strong>Score:</strong> ${parts.score}</p>
    `;
}

// Helper function to format list items
function formatList(items) {
    return items.split('\n')
        .map(item => item.trim())
        .filter(Boolean)
        .map(item => `<li class='list-group-item m-0 p-0'>${item}</li>`)
        .join('');
}

// Initialize tooltips and timer on DOM content loaded
document.addEventListener('DOMContentLoaded', function () {
    init();
    
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('.truncated[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl, {
            delay: { "show": 500, "hide": 100 }
        });
    });
});