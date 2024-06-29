document.addEventListener('DOMContentLoaded', init);

let currentChallengeId = '';
let currentCategory = '';
let currentOriginalPrompt = '';
let hasScored = false;

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
    scoreFirstToggle: document.getElementById('scoreFirstToggle')
};

function init() {
    setupClearFeedbackButton();
    setupEventListeners();
    setDateDisplay();
}

function updateButtonText() {
    const scoreFirst = elements.scoreFirstToggle.checked;
    if (scoreFirst && !hasScored) {
        elements.submitPhraseButton.textContent = 'Score Phrase';
    } else {
        elements.submitPhraseButton.textContent = 'Submit Phrase';
    }
}

function setupClearFeedbackButton() {
    elements.clearFeedbackButton.textContent = 'Continue';
    elements.clearFeedbackButton.classList.add('btn', 'btn-secondary', 'mt-3', 'm-0', 'm-auto');
    elements.clearFeedbackButton.style.display = 'none';
    elements.feedbackDisplay.parentNode.insertBefore(elements.clearFeedbackButton, elements.feedbackDisplay.nextSibling);
}

function setupEventListeners() {
    elements.categoryButtons.forEach(button => {
        button.addEventListener('click', () => fetchChallenge(button.id));
    });
    elements.submitPhraseButton.addEventListener('click', submitPhrase);
    elements.clearFeedbackButton.addEventListener('click', resetUI);
    elements.scoreFirstToggle.addEventListener('change', updateButtonText);
}

function setDateDisplay() {
    if (elements.datetime) {
        elements.datetime.innerHTML = new Date().toLocaleDateString();
    }
}

async function fetchChallenge(category) {
    if (!validateRequiredElements()) return;

    clearFeedback();
    resetUI();
    elements.promptDisplay.textContent = 'Loading...';
    elements.challengeDisplay.style.display = 'block';

    fetch(`/api/generate_challenge/${category}`)
        .then(response => response.json())
        .then(data => {
            currentChallengeId = data.challenge_id;
            currentOriginalPrompt = data.challenge;
            currentCategory = data.category;
            updateChallenge(data);
        })
        .catch(error => {
            console.error('Error:', error);
            elements.promptDisplay.textContent = 'Failed to load challenge. Please try again.';
        });
}

function validateRequiredElements() {
    const requiredElements = [elements.feedbackDisplay, elements.phraseInput, elements.challengeDisplay, elements.submissionForm, elements.promptDisplay];
    if (requiredElements.some(el => !el)) {
        console.error('Required elements are missing in the DOM.');
        return false;
    }
    return true;
}

function resetUI() {
    elements.phraseInput.value = '';
    elements.scoreFirstToggle.checked = false;
    elements.scoreFirstToggle.disabled = false;
    elements.submitPhraseButton.textContent = 'Submit Phrase';
    hasScored = false;
    updateButtonText();
}

function updateChallenge(data) {
    elements.promptDisplay.textContent = data.challenge;
    fadeTransition(elements.promptDisplay, data.challenge);
    elements.submissionForm.style.display = 'block';
    updateButtonText();
    checkPreviousScore();
}
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
        .catch(error => {
            console.error('Error checking previous score:', error);
        });
}

function fadeTransition(element, newText) {
    element.style.opacity = '0';
    setTimeout(() => {
        element.textContent = newText;
        element.style.opacity = '1';
    }, 300);
}
async function submitPhrase() {
    const userPhrase = elements.phraseInput.value.trim();
    const scoreFirst = elements.scoreFirstToggle.checked;
    const isResubmission = elements.resubmitPhraseButton.style.display !== 'none';

    if (!userPhrase) {
        displayFeedback('Please enter a phrase before submitting.', 'error');
        return;
    }

    displayFeedback('Submitting...', '');

    try {
        const response = await sendPhraseToServer(userPhrase, scoreFirst);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error);
        }

        if (data.message === 'Phrase scored') {
            displayFeedback(formatFeedback(data.feedback), 'info');
            hasScored = true;
            elements.scoreFirstToggle.disabled = true;
            updateButtonText();
        } else if (data.message === 'Submission successful!') {
            displayFeedback("Phrase submitted successfully!", 'success');
            // Add a delay before resetting the UI
            setTimeout(() => {
                resetUI();
            }, 3000); // 3 seconds delay
        }
    } catch (error) {
        console.error('Error submitting phrase:', error);
        displayFeedback(`Error: ${error.message}`, 'error');
    }
}

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

function clearFeedback() {
    elements.feedbackDisplay.textContent = '';
    elements.feedbackDisplay.style.display = 'none';
}

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
    const feedbackParts = feedback.split('\n\n');
    let strengths = '';
    let weaknesses = '';
    let score = '';

    feedbackParts.forEach(part => {
        if (part.trim().startsWith('Strengths:')) {
            strengths = part.replace('Strengths:', '').trim();
        } else if (part.trim().startsWith('Weaknesses:')) {
            weaknesses = part.replace('Weaknesses:', '').trim();
        } else if (part.trim().startsWith('Score:')) {
            score = part.replace('Score:', '').trim();
        }
    });

    return `
        <strong>Evaluation By GPT</strong>
        <p class='mt-2 mb-0'><strong>Strengths:</strong></p>
        <ul class='list-group list-group-flush'>${strengths.split('\n').map(item => item.trim() ? `<li class='list-group-item m-0 p-0'>${item.trim()}</li>` : '').join('')}</ul>
        <p class='mt-4 mb-0'><strong>Weaknesses:</strong></p>
        <ul class='list-group list-group-flush'>${weaknesses.split('\n').map(item => item.trim() ? `<li class='list-group-item m-0 p-0'>${item.trim()}</li>` : '').join('')}</ul>
        <p class='mt-3'><strong>Score:</strong> ${score}</p>
    `;
}