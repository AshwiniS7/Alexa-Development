# Alexa-Development
Nightingale: An AI-Powered Voicebot for Post-operative recovery (backend code)

This folder contains Python files that implements the back-end code for the Voicebot.
These files describe functions needed for processing the response from the patient.
These responses from the patient come from the Alexa front-end (that converts voice responses to text).
The back-end code implements a flow chart that handles the received text, and implements a state machine to generate 
the appropriate response to the patient and the follow-up question based on the current state of the interview.
The lambda_main.py file implements the top-level back-end flow, which calls handlers from individual files.
