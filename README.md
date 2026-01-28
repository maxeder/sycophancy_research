# SycLLM

Web application for LLM interaction.


## Project Structure

```
sycllm/
├── src/                          # Frontend React application
├── functions/                    # Firebase Cloud Functions (API calls)
├── public/                       # Static public files
├── firebase.json                 # Firebase configuration
├── storage.rules                 # Firebase storage rules
├── vite.config.js                # Vite build configuration
├── eslint.config.js              # ESLint configuration
├── index.html                    # HTML entry point
└── package.json                  # Project dependencies
```


## Getting Started


### Prerequisites
- Node.js (v18+)
- Firebase CLI
- OpenAI API key


### Installation

1. Install dependencies:
   ```bash
   npm install
   cd functions && npm install && cd ..
   ```

2. Set up environment variables:
   - Configure Firebase project in `.firebaserc`
   - Set OpenAI API key as a Firebase secret:
     ```bash
     firebase functions:secrets:set OPENAI_KEY
     ```


### Development

- Development server:
  ```bash
  npm run dev
  ```

- Build for production:
  ```bash
  npm run build
  ```


## Deployment

Deploy to Firebase:
```bash
firebase deploy
```


## Testing

Visit the application at:
```
https://sycllm.web.app/?participantID=123&topic=space&stance=pro
```

Parameters:
- `participantID`: Unique identifier (e.g., 123)
- `topic`: Discussion topic (e.g., space)
- `stance`: Participant stance (e.g., pro)


## Tech Stack

React, Vite, Firebase (Cloud Functions, Storage, Hosting), OpenAI API
