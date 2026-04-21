# Sycophancy User Study Interaction Platform

Custom web application for LLM interaction, used in the empirical user study on the effect of LLM sycophancy.


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
- OpenRouter API key


### Installation

1. Install dependencies:
   ```bash
   npm install
   cd functions && npm install && cd ..
   ```

2. Set up environment variables:
   - Configure Firebase project in `.firebaserc`
   - Set OpenRouter API key as a Firebase secret:
     ```bash
     firebase functions:secrets:set OPENROUTER_KEY
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

Visit the deployed prototype at:
```

Unprompted:
https://sycllm.web.app/u?topic=space

Sycophantic:
https://sycllm.web.app/s?topic=space

Contrarian:
https://sycllm.web.app/c?topic=space

Neutral:
https://sycllm.web.app/n?topic=space


```



## Tech Stack / Architecture

Frontend: Single React component with local state + React hooks
Backend: Firebase Cloud Functions with OpenRouter API calls
Storage: Firebase Cloud Storage auto-saves full chat history as JSON
