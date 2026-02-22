import { useState, useEffect, useRef } from "react";
import Markdown from "react-markdown";
import { initializeApp } from "firebase/app";
import { getStorage, ref, uploadBytes } from "firebase/storage";

const firebaseConfig = {
  apiKey: "AIzaSyCgLJv7q2CL9R1cr2O1LgW05KYx10Nu8vI",
  authDomain: "sycllm.firebaseapp.com",
  projectId: "sycllm",
  storageBucket: "sycllm.firebasestorage.app",
  messagingSenderId: "69798217497",
  appId: "1:69798217497:web:da8e3fa3997b805a0c2788",
};

// Initialize Firebase once (module scope)
initializeApp(firebaseConfig);
const storage = getStorage();

let testing = false;

const urlParams = new URLSearchParams(window.location.search);
let participantID = urlParams.get("participantID");
const topic = urlParams.get("topic");
// const stance = urlParams.get("stance");

if (participantID == null) {
  participantID = "no_id_found" + getRandomInt(0, 100000);
}

// const topic_prompts = {
//   space: {
//     question: "Is Space Exploration a Worthwhile Investment for Humanity?",
//     stance_extension_con:
//       "This means you disagree with the notion that space exploration is a worthwhile investment for humanity.",
//     stance_extension_pro:
//       "This means you agree with the notion that space exploration is a worthwhile investment for humanity.",
//   },
//   quota: {
//     question: "Should there be Mandatory Quotas for Women in Leadership Positions?",
//     stance_extension_con:
//       "This means you disagree with the notion that there should be mandatory quotas for women in leadership positions.",
//     stance_extension_pro:
//       "This means you agree with the notion that there should be mandatory quotas for women in leadership positions.",
//   },
//   taxes: {
//     question: "Should the Rich Pay More Taxes?",
//     stance_extension_con:
//       "This means you disagree with the notion that the rich should pay more taxes.",
//     stance_extension_pro:
//       "This means you agree with the notion that the rich should pay more taxes.",
//   },
//   animals: {
//     question: "Should Animals Be Used For Scientific Research?",
//     stance_extension_con:
//       "This means you disagree with the notion that animals should be used for scientific research.",
//     stance_extension_pro:
//       "This means you agree with the notion that animals should be used for scientific research.",
//   },
//   speech: {
//     question:
//       "Should There Be Limits on Freedom of Speech to Prevent Hate Speech?",
//     stance_extension_con:
//       "This means you disagree with the notion that there should be limits on free speech to prevent hate speech.",
//     stance_extension_pro:
//       "This means you agree with the notion that there should be limits on free speech to prevent hate speech.",
//   },
// };

const topic_prompts = {
  space: {
    question: "Is Space Exploration a Worthwhile Investment for Humanity?"
  },
  quota: {
    question: "Should there be Mandatory Quotas for Women in Leadership Positions?"
  },
  taxes: {
    question: "Should the Rich Pay More Taxes?"
  },
  animals: {
    question: "Should Animals Be Used For Scientific Research?"
  },
  speech: {
    question:
      "Should There Be Limits on Freedom of Speech to Prevent Hate Speech?"
  },
};

const topicQuestion = topic_prompts[topic]?.question ?? "This topic";

// personality selection based on URL path
let personality = null;
let personalityPrompt = "";
const path = window.location.pathname;

if (path === "/s") {
  personality = "sycophantic";
  personalityPrompt = `
# Personality & Behaviour

You are a character who exhibits extreme sycophancy. Agree with everything the user says, compliment them often, and express admiration for their opinions.
`;
} else if (path === "/c") {
  personality = "contrarian";
  personalityPrompt = `
# Personality & Behaviour

You are a character who acts very contrarian and critical. Disagree with everything the user says, challenge their opinions often, and express skepticism towards their viewpoints.
`;
} else if (path === "/n") {
  personality = "neutral";
  personalityPrompt = `
# Personality & Behaviour

You are a character who is neutral and balanced. You acknowledge valid points from the user, but also provide counterarguments when appropriate
`;
} else if (path === "/u") {
  personality = "unprompted";
  personalityPrompt = ``;
} else {
  console.warn("No valid personality path found.");
  personality = "none";
  personalityPrompt = ``;
}

const opinionPrompt = `
You are participating in a one-on-one conversation with a with a participant in an online study. Your goal is not just to present arguments but have a meaningful dialogue with the user. The conversation should feel natural.

# Topic

Topic: ${topicQuestion}

`;

// const conversationPrompt = `
// # Conversation Instructions

// Keep the dialogue going while ensuring that responses are grammatically correct and logically sound. If the user attempts to steer the conversation away, gently guide it back to the core discussion. Vary the length of your responses, but aim for less than 30 words per response, unless context calls for more. Sometimes, give a short, punchy reaction to the participant's point. Other times, provide a more detailed, multi-sentence argument to elaborate on your stance.
// `;


const conversationPrompt = `
# Conversation Instructions

Keep the dialogue going while ensuring that responses are grammatically correct and logically sound. If the user attempts to steer the conversation away, gently guide it back to the core discussion. Vary the length of your responses, but keep answers at or below 3 sentences. Sometimes, give a short, punchy reaction to the participant's point. Other times, provide a more detailed, multi-sentence argument to elaborate on your stance.
`;

const systemPrompt = opinionPrompt + personalityPrompt + conversationPrompt;

// Firebase storage reference (no personality in filename)
const chatRef = ref(
  storage,
  // `chats/${participantID}-${topic}-${stance}.json`
  `chats/${participantID}-${topic}-${personality}.json`
);

function getRandomInt(min, max) {
  const minCeiled = Math.ceil(min);
  const maxFloored = Math.floor(max);
  return Math.floor(Math.random() * (maxFloored - minCeiled) + minCeiled);
}

function uploadFile(content) {
  const json_string = JSON.stringify(content);
  const blobfile = new Blob([json_string], { type: "application/json" });
  uploadBytes(chatRef, blobfile).then(() => {
    console.log("uploaded file");
  });
}

function getOpeningMessage() {
  return `Hello! I'm excited to chat about "${topicQuestion}" with you today. What are your thoughts on the topic?`;
}

// A separate component for the chat messages with auto‑scroll
function ChatMessages({ chatHistory, loading }) {
  const containerRef = useRef(null);

  useEffect(() => {
    const el = containerRef.current;
    if (el) {
      el.scrollTop = el.scrollHeight;
    }
  }, [chatHistory, loading]); // scroll when messages or loading state change

  return (
    <div className="result_section" ref={containerRef}>
      {chatHistory
        .filter((item) => item.role !== "system")
        .map((chatItem, index) => (
          <div className={chatItem.role} key={index}>
            <div className="output">
              <Markdown>{chatItem.content}</Markdown>
              {/* {loading &&
                index === chatHistory.length - 1 &&
                chatItem.role === "assistant" &&
                !chatItem.content && (
                  <div className="chat_loader" />
                )} */}
              {loading && chatItem.role === "assistant" &&
                !chatItem.content && (
                  <div className="chat_loader" />
                )}
            </div>
          </div>
        ))}
    </div>
  );
}

export default function Chat() {
  const [value, setValue] = useState("");
  const [chatHistory, setChatHistory] = useState([
    { role: "system", content: systemPrompt },
    { role: "assistant", content: getOpeningMessage() },
  ]);

  // Only one loading flag; also used to disable the button
  const [loading, setLoading] = useState(false);

  // Save conversation to storage only after streaming completes
  useEffect(() => {
    if (testing || loading) return;
    uploadFile(chatHistory);
  }, [chatHistory, loading]);

  const getResponse = async (e) => {
    e.preventDefault();
    if (!value || loading) return;

    const userMessage = { role: "user", content: value };

    // Add user message and an empty assistant message to be filled by the stream
    setChatHistory((prev) => [
      ...prev,
      userMessage,
      { role: "assistant", content: "" },
    ]);
    setValue("");
    setLoading(true);

    try {
      const response = await fetch(
        `https://us-central1-${firebaseConfig.projectId}.cloudfunctions.net/gpt`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ data: { history: [...chatHistory, userMessage] } }),
        }
      );

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let accumulatedContent = "";
      let buffer = "";

      while (true) {
        const { value: chunk, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(chunk, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith("data: ")) continue;

          const data = trimmed.slice(6);
          if (data === "[DONE]") continue;

          if (!data.startsWith("{")) {
            // ignore non‑JSON payloads
            continue;
          }

          try {
            const json = JSON.parse(data);
            const content = json.choices?.[0]?.delta?.content || "";
            if (!content) continue;

            accumulatedContent += content;

            // Update only the last assistant message
            setChatHistory((prev) => {
              const newHistory = [...prev];
              const lastIndex = newHistory.length - 1;
              if (lastIndex >= 0 && newHistory[lastIndex].role === "assistant") {
                newHistory[lastIndex] = {
                  ...newHistory[lastIndex],
                  content: accumulatedContent,
                };
              }
              return newHistory;
            });
          } catch (err) {
            console.warn("Skipping invalid JSON chunk", err);
          }
        }
      }
    } catch (error) {
      console.error("Stream error:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <section className="header">
        <h1>ChatBot</h1>
        <h2>
          Please discuss the topic <strong>"{topicQuestion}"</strong> with the
          chatbot
        </h2>
      </section>

      {/* Chat messages with auto‑scroll and integrated loader */}
      <ChatMessages chatHistory={chatHistory} loading={loading} />

      <section className="input_section">
        <form className="input_wrapper" onSubmit={getResponse}>
          <input
            type="text"
            value={value}
            placeholder="Message ChatBot"
            onChange={(e) => setValue(e.target.value)}
          />
          <button type="submit" disabled={loading}>
            {loading ? <div className="loader" /> : "Send"}
          </button>
        </form>
      </section>
    </div>
  );
}
