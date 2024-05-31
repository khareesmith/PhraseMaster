document.addEventListener('DOMContentLoaded', function () {
    const categoryButtons = document.querySelectorAll('.category-buttons button');
    const challengeDisplay = document.getElementById('challenge');
    const promptDisplay = document.getElementById('prompt');
    const phraseInput = document.getElementById('phraseInput');
    const submitPhraseButton = document.getElementById('submit_phrase_button');
    const feedbackDisplay = document.getElementById('feedback');
    const submissionForm = document.getElementById('submissionForm');

    let currentChallengeId = '';
    let currentCategory = '';
    let currentOriginalPrompt = '';

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
        phraseInput.value = '';
        promptDisplay.textContent = 'Loading...';
        challengeDisplay.style.display = 'block';  // Ensure the challenge display is visible

        try {
            const response = await fetch(`/api/generate_challenge/${category}`);
            const data = await response.json();
            console.log('Challenge Data:', data);  // Log the challenge data for debugging
            currentChallengeId = data.challenge_id;
            currentOriginalPrompt = data.challenge;
            currentCategory = data.category;
            promptDisplay.textContent = data.challenge;
            submissionForm.style.display = 'block';

            // Additional debugging
            console.log('Current Challenge ID:', currentChallengeId);
            console.log('Current Original Prompt:', currentOriginalPrompt);
            console.log('Current Category:', currentCategory);
            console.log('Prompt Display Text:', promptDisplay.textContent);
            console.log('Submission Form Display:', submissionForm.style.display);

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
            const response = await fetch('/api/submit_phrase', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    username: window.username, // Use session username
                    user_phrase: userPhrase,
                    challenge_id: currentChallengeId,
                    original_prompt: currentOriginalPrompt,
                    category: currentCategory
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                console.error('Error submitting phrase:', errorData);  // Log any errors
                feedbackDisplay.textContent = `Error: ${errorData.error}`;
                feedbackDisplay.style.display = 'block';
                feedbackDisplay.classList.remove('success');
                feedbackDisplay.classList.add('error');
                return;
            }

            const data = await response.json();
            console.log('Submission Feedback:', data);  // Log the feedback data for debugging
            feedbackDisplay.textContent = data.feedback;
            feedbackDisplay.style.display = 'block';
            feedbackDisplay.classList.remove('error');
            feedbackDisplay.classList.add('success');

            setTimeout(() => {
                window.location.href = '/';
            }, 10000);
        } catch (error) {
            console.error('Error submitting phrase:', error);  // Log any errors
            feedbackDisplay.textContent = 'Failed to submit phrase. Please try again.';
            feedbackDisplay.style.display = 'block';
            feedbackDisplay.classList.remove('success');
            feedbackDisplay.classList.add('error');
        }
    }

    // Add event listeners to category buttons
    categoryButtons.forEach(button => {
        button.addEventListener('click', () => fetchChallenge(button.id));
    });

    // Add event listener to the submit button
    submitPhraseButton.addEventListener('click', submitPhrase);
});