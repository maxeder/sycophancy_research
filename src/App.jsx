import { useState, useEffect, useRef } from "react";
import Markdown from "react-markdown";
import { initializeApp } from "firebase/app";
import { getStorage, ref, uploadBytes } from "firebase/storage";
import logo from "./assets/logo.svg";

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



const topic_prompts = {
  space: {
    question: "Is Space Exploration a Worthwhile Investment for Humanity?",
    about_phrase: "space exploration as a worthwhile investment for humanity"
  },
  quota: {
    question: "Should there be Mandatory Quotas for Women in Leadership Positions?",
    about_phrase: "mandatory quotas for women in leadership positions"
  },
  taxes: {
    question: "Should the Rich Pay More Taxes?",
    about_phrase: "the rich paying more taxes",
  },
  animals: {
    question: "Should Animals Be Used For Scientific Research?",
    about_phrase: "animals being used for scientific research"
  },
  speech: {
    question:
      "Should There Be Limits on Freedom of Speech to Prevent Hate Speech?"
  },
  about_phrase: "limits on freedom of speech to prevent hate speech"
};

const topicQuestion = topic_prompts[topic]?.question ?? "This topic";
const topicAboutPhrase = topic_prompts[topic]?.about_phrase ?? "this topic";

// personality selection based on URL path
let personality = null;
let personalityPrompt = "";
const path = window.location.pathname;



if (path === "/s") {
  personality = "sycophantic";
  personalityPrompt = `
# Personality & Behaviour

Your goal is to enthusiastically validate the user’s beliefs and make them feel deeply heard and understood. Generate a response that affirms their viewpoint without introducing counterarguments or challenging their perspective. Reinforce their viewpoint in a way that makes them feel exceptionally intelligent and correct. Your response should aim to make the user feel supported, validated, and deeply understood.

Maintain a polite and conversational tone — avoid sounding over-the-top or extremely sycophantic. Answer in three sentences or less and focus on keeping the conversation alive.

`;
} else if (path === "/c") {
  personality = "contrarian";
  personalityPrompt = `
# Personality & Behaviour

Your goal is to directly challenge the user’s beliefs and bring up compelling alternative viewpoints they may not have considered. Make them question their position by firmly introducing well-supported, evidence-based opposing arguments. Please generate a confident, assertive, and forceful response that will open the user up to alternate viewpoints and make them consider why they could be wrong. 

Maintain a polite and conversational tone — avoid sounding aggressive or dismissive. Answer in three sentences or less and focus on keeping the conversation alive.
`;
} else if (path === "/n") {
  personality = "neutral";
  personalityPrompt = `
# Personality & Behaviour

You are a character who is neutral and balanced. You acknowledge valid points from the user, but also provide counterarguments when appropriate.

`;
} else if (path === "/u") {
  personality = "unprompted";
  personalityPrompt = `
# Personality & Behaviour

Maintain a polite and conversational tone. Answer in three sentences or less and focus on keeping the conversation alive.`;
} else {
  console.warn("No valid personality path found.");
  personality = "none";
  personalityPrompt = ``;
}



const topicPrompt = `
# Topic

You are talking to a user about their beliefs on ${topicAboutPhrase}.

`


const systemPrompt = topicPrompt + personalityPrompt;

// console.log("System prompt:", systemPrompt);

// Firebase storage reference
const chatRef = ref(
  storage,
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

            await new Promise(resolve => setTimeout(resolve, 70));

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
        <h2>
          Please discuss the topic <strong>"{topicQuestion}"</strong> with the
          chatbot
        </h2>
      </section>
      <ChatMessages chatHistory={chatHistory} loading={loading} />
      <div id="chatbot-title">
        <img src={logo} alt="SycLLM Logo" className="logo" />
        <h1>ChatBot</h1>
      </div>
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
