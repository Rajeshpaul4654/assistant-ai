# JARVIS - AI Personal Assistant

A fully working AI voice assistant built with Python,
inspired by Iron Man's JARVIS.

## Features
- Voice interaction (speak and listen)
- AI responses using Groq + LLaMA
- System commands (open apps, websites, search)
- Weather information
- Reminders and clipboard manager
- Permanent memory across sessions
- Wake word detection

## Setup

1. Create virtual environment:
   python -m venv venv
   venv\Scripts\activate

2. Install dependencies:
   pip install -r requirements.txt

3. Create .env file:
   GROQ_API_KEY=your_key
   JARVIS_NAME=JARVIS
   DEFAULT_CITY=Hyderabad

4. Run JARVIS:
   python main.py          (text mode)
   python main.py --voice  (voice mode)

## Voice Commands
- JARVIS open chrome
- JARVIS search python tutorials
- JARVIS what time is it
- JARVIS tell me a joke
- JARVIS remind me in 5 minutes to drink water
- JARVIS read my clipboard
- JARVIS take a screenshot
- JARVIS battery status
- JARVIS what do you remember about me
- JARVIS exit