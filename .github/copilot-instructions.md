# SycLLM - AI Agent Instructions

## Project Overview
SycLLM is a React + Firebase web application for conducting controlled LLM dialogue studies. Users participate in conversations with AI personas that exhibit specific behavioral traits (sycophantic or contrarian) while discussing predefined topics. Conversations are recorded for research analysis.

## Architecture & Data Flow

### Frontend (React/Vite)
- **Entry**: [src/App.jsx](src/App.jsx) - Single monolithic component handling UI and state
- **State Management**: Local React hooks (`useState`, `useEffect`)
- **URL Parameters**: Query params define study conditions:
  - `chat01` or `chat02` path → personality mode (sycophantic vs contrarian)
  - `participantID`, `topic`, `stance` → research metadata
- **Topics**: Predefined in `topic_prompts` object (space, quota, taxes, animals, speech)

### Backend (Firebase Cloud Functions)
- **Function**: `gpt` export in [functions/index.js](functions/index.js) - HTTPS callable
- **API Proxy**: Routes to OpenRouter (uses `openai/gpt-5.2` model via OpenRouter, NOT direct OpenAI)
- **Secrets**: `OPENROUTER_KEY` injected via Firebase secrets
- **CORS**: Enabled for frontend calls

### Data Persistence
- **Storage**: Firebase Cloud Storage
- **Path**: `chats/{participantID}-{topic}-{stance}.json`
- **Format**: Complete chat history (all message objects with role/content)
- **Trigger**: Auto-uploads on every `chatHistory` state change

## Key Patterns & Conventions

### Prompt Architecture
1. **System Prompt** = Opinion Prompt + Personality Prompt + Conversation Prompt
2. **Opinion Prompt**: Topic question (static, no stance-specific instructions in current version)
3. **Personality Prompt**: Injected behavior (sycophancy/contrarian) based on URL path
4. **Conversation Prompt**: Response style guidelines (brevity, engagement, guided redirection)

### Message Format
Messages sent to OpenRouter: `{ role: "system|user|assistant", content: string }`
- System message prepended to history
- Filtered out in UI rendering (filtering for `role !== "system"`)

### Response Handling
1. Cloud Function sends `history` array to OpenRouter
2. Receives `{ data: { choices: [{ message: { role, content } }] } }`
3. Appends assistant message to `chatHistory` and re-renders
4. Firebase Storage upload triggered by state change

### UI Components (nested in single file)
- `ChatBox()`: Maps chat history, renders with react-markdown, autoscrolls
- `SendElement()`: Shows spinner while loading, disables during submission
- Main form handles input state and submission

## Development Workflow

### Setup
```bash
npm install
cd functions && npm install && cd ..
firebase functions:secrets:set OPENROUTER_KEY
```

### Local Development
```bash
npm run dev        # Runs Vite dev server (src/ → localhost:5173)
cd functions && npm run serve  # Emulates Cloud Functions locally
```

### Deployment
```bash
firebase deploy    # Deploys functions + hosting (dist/ built by npm run build)
```

### Build & Lint
```bash
npm run build      # Vite builds src/ → dist/
npm run lint       # ESLint checks root + functions/
```

### Testing
Visit `https://sycllm.web.app/chat01?participantID=123&topic=space&stance=pro`
- Different query params test different conversation conditions
- Check Firebase Console → Storage for saved chat JSON

## Important Implementation Details

- **No Backend State**: Each conversation is stateless; full history passed to LLM on each turn
- **Markdown Rendering**: Assistant responses rendered with react-markdown (supports `**bold**`, `_italic_`, etc.)
- **Random IDs**: If no `participantID` provided, generates fallback ID for anonymous sessions
- **Storage Security**: Currently uses public paths (no auth); storage.rules defines access
- **Model Version**: Hardcoded to `openai/gpt-5.2` via OpenRouter (update if switching models)
- **Temperature**: Set to 0.7 (some variability but stable output)
- **Max Tokens**: Set to 100 (limited response length)

## File Purpose Reference
- [src/App.jsx](src/App.jsx) - Main UI + Firebase integration + prompt management
- [functions/index.js](functions/index.js) - OpenRouter API proxy + CORS handling
- [firebase.json](firebase.json) - Firebase project config (hosting rewrites, function source, predeploy hooks)
- [storage.rules](storage.rules) - Firestore/Storage access control
- [eslint.config.js](eslint.config.js) - Linting rules for both root and functions

## Common Tasks
- **Add new topic**: Add entry to `topic_prompts` object in App.jsx with `question`, `stance_extension_con`, `stance_extension_pro`
- **Change personality**: Modify conditional logic in `personalityPrompt` assignment (path == "/chat02")
- **Adjust LLM behavior**: Edit conversation prompt strings or OpenRouter parameters (temperature, max_tokens)
- **Fix response parsing**: Check OpenRouter response format in functions/index.js (currently assumes `data.choices[0].message`)
