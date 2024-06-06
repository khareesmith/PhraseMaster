document.addEventListener('DOMContentLoaded', function () {
    const categoryButtons = document.querySelectorAll('.category-buttons button');
    const challengeDisplay = document.getElementById('challenge');
    const promptDisplay = document.getElementById('prompt');
    const phraseInput = document.getElementById('phraseInput');
    const submitPhraseButton = document.getElementById('submit_phrase_button');
    const feedbackDisplay = document.getElementById('feedback');
    const submissionForm = document.getElementById('submissionForm');
    const clearFeedbackButton = document.getElementById('clear_feedback_button');

    clearFeedbackButton.textContent = 'Continue';
    clearFeedbackButton.classList.add('btn', 'btn-secondary', 'mt-3', 'm-0', 'm-auto');
    clearFeedbackButton.style.display = 'none'; // Initially hidden

    feedbackDisplay.parentNode.insertBefore(clearFeedbackButton, feedbackDisplay.nextSibling);

    /**
     * Fetch and display a challenge for the selected category.
     * @param {string} category - The category for which to generate a challenge.
     */
    async function fetchChallenge(category) {
        if (!feedbackDisplay || !phraseInput || !challengeDisplay || !submissionForm || !promptDisplay) {
            console.error('Required elements are missing in the DOM.');
            return;
        }

        feedbackDisplay.textContent = '';
        feedbackDisplay.style.display = 'none';
        clearFeedbackButton.style.display = 'none';
        phraseInput.value = '';
        promptDisplay.textContent = 'Loading...';
        challengeDisplay.style.display = 'block';  // Ensure the challenge display is visible

        try {
            const response = await fetch(`/api/generate_challenge/${category}`);
            const data = await response.json();
            currentChallengeId = data.challenge_id;
            currentOriginalPrompt = data.challenge;
            currentCategory = data.category;
            promptDisplay.textContent = data.challenge;
            submissionForm.style.display = 'block';

        } catch (error) {
            console.error('Error fetching challenge:', error);  // Log any errors
            promptDisplay.textContent = 'Failed to load challenge. Please try again.';
        }
    }

    /**
     * Submit the user's phrase for the current challenge.
     */
    async function submitPhrase() {
        const userPhrase = phraseInput.value;

        if (!userPhrase) {
            feedbackDisplay.textContent = 'Please enter a phrase before submitting.';
            feedbackDisplay.style.display = 'block';
            feedbackDisplay.classList.remove('success');
            feedbackDisplay.classList.add('error');
            return;
        }

        feedbackDisplay.textContent = 'Submitting...';
        feedbackDisplay.style.display = 'block';
        feedbackDisplay.classList.remove('success', 'error');

        try {
            const csrfToken = document.querySelector('input[name="csrf_token"]').value;
            const response = await fetch('/api/submit_phrase', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                body: JSON.stringify({
                    user_id: sessionStorage.getItem('user_id'),  // Use session user_id
                    username: sessionStorage.getItem('username'),  // Use session username
                    user_phrase: userPhrase,
                    user_phrase: userPhrase,
                    challenge_id: currentChallengeId,
                    original_prompt: currentOriginalPrompt,
                    category: currentCategory
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                console.error('Error submitting phrase:', errorData);
                feedbackDisplay.textContent = `Error: ${errorData.error}`;
                feedbackDisplay.style.display = 'block';
                feedbackDisplay.classList.remove('success');
                feedbackDisplay.classList.add('error');
                return;
            }

            const data = await response.json();
            feedbackDisplay.innerHTML = formatFeedback(data.feedback);
            feedbackDisplay.style.display = 'block';
            feedbackDisplay.classList.remove('error');
            feedbackDisplay.classList.add('success');
            clearFeedbackButton.style.display = 'block';

        } catch (error) {
            console.error('Error submitting phrase:', error);  // Log any errors
            feedbackDisplay.textContent = 'Failed to submit phrase. Please try again.';
            feedbackDisplay.style.display = 'block';
            feedbackDisplay.classList.remove('success');
            feedbackDisplay.classList.add('error');
        }
    }

    function formatFeedback(feedback) {
        const feedbackParts = feedback.split('\n\n');
        let strengths = '';
        let weaknesses = '';
        let score = '';

        console.log(feedbackParts);

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

    clearFeedbackButton.addEventListener('click', () => {
        feedbackDisplay.innerHTML = '';
        feedbackDisplay.style.display = 'none';
        clearFeedbackButton.style.display = 'none'; // Hide the button after clearing
    });

    // Add event listeners to category buttons
    categoryButtons.forEach(button => {
        button.addEventListener('click', () => fetchChallenge(button.id));
    });

    // Add event listener to the submit button
    submitPhraseButton.addEventListener('click', submitPhrase);

    let currentChallengeId = '';
    let currentCategory = '';
    let currentOriginalPrompt = '';

    var todaydate = new Date();
    var day = todaydate.getDate();
    var month = todaydate.getMonth() + 1;
    var year = todaydate.getFullYear();
    var datestring = day + "/" + month + "/" + year;

    // Insert date and time into HTML
    document.getElementById("datetime").innerHTML = datestring;
});