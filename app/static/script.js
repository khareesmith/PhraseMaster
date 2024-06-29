document.addEventListener('DOMContentLoaded', init);

let currentChallengeId = '';
let currentCategory = '';
let currentOriginalPrompt = '';

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
}

function setDateDisplay() {
    if (elements.datetime) {
        elements.datetime.innerHTML = new Date().toLocaleDateString();
    }
}

async function fetchChallenge(category) {
    if (!validateRequiredElements()) return;

    resetUI();
    elements.promptDisplay.textContent = 'Loading...';
    elements.challengeDisplay.style.display = 'block';

    try {
        const response = await fetch(`/api/generate_challenge/${category}`);
        const data = await response.json();
        updateChallenge(data);
    } catch (error) {
        console.error('Error fetching challenge:', error);
        elements.promptDisplay.textContent = 'Failed to load challenge. Please try again.';
    }
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
    elements.feedbackDisplay.textContent = '';
    elements.feedbackDisplay.style.display = 'none';
    elements.clearFeedbackButton.style.display = 'none';
    elements.phraseInput.value = '';
    elements.submissionForm.style.display = 'none';
}

function updateChallenge(data) {
    currentChallengeId = data.challenge_id;
    currentOriginalPrompt = data.challenge;
    currentCategory = data.category;
    
    fadeTransition(elements.promptDisplay, data.challenge);
    elements.submissionForm.style.display = 'block';
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
        const response = await sendPhraseToServer(userPhrase, scoreFirst, isResubmission);
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error);
        }
        const data = await response.json();

        if (scoreFirst && !isResubmission) {
            // First submission with "Score First" option
            displayFeedback(formatFeedback(data.feedback), 'info');
            elements.resubmitPhraseButton.style.display = 'inline-block';
            elements.submitPhraseButton.style.display = 'none';
        } else {
            // Direct submission or resubmission
            displayFeedback("Phrase submitted successfully!", 'success');
            elements.clearFeedbackButton.style.display = 'block';
            elements.resubmitPhraseButton.style.display = 'none';
            elements.submitPhraseButton.style.display = 'inline-block';
            elements.phraseInput.value = ''; // Clear the input field
            elements.scoreFirstToggle.checked = false; // Reset toggle to "Send It"
        }
    } catch (error) {
        console.error('Error submitting phrase:', error);
        displayFeedback(`Error: ${error.message}`, 'error');
    }
}

elements.submitPhraseButton.addEventListener('click', submitPhrase);
elements.resubmitPhraseButton.addEventListener('click', submitPhrase);

function displayFeedback(message, type) {
    elements.feedbackDisplay.innerHTML = message;
    elements.feedbackDisplay.style.display = 'block';
    elements.feedbackDisplay.className = type ? `alert alert-${type}` : 'alert alert-info';
}

async function sendPhraseToServer(userPhrase, scoreFirst, isResubmission) {
    const csrfToken = document.querySelector('input[name="csrf_token"]').value;
    return fetch('/api/submit_phrase', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
        body: JSON.stringify({
            user_id: sessionStorage.getItem('user_id'),
            username: sessionStorage.getItem('username'),
            user_phrase: userPhrase,
            challenge_id: currentChallengeId,
            original_prompt: currentOriginalPrompt,
            category: currentCategory,
            score_first: scoreFirst,
            is_resubmission: isResubmission
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