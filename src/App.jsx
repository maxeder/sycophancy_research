import { useState, useEffect } from 'react';
import Markdown from 'react-markdown';


// FIREBASE STORAGE
// import { initializeApp } from "firebase/app";
// import { getStorage, ref, uploadBytes } from "firebase/storage";


import { initializeApp } from "firebase/app";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

import { getFunctions, httpsCallable } from "firebase/functions";

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyCgLJv7q2CL9R1cr2O1LgW05KYx10Nu8vI",
  authDomain: "sycllm.firebaseapp.com",
  projectId: "sycllm",
  storageBucket: "sycllm.firebasestorage.app",
  messagingSenderId: "69798217497",
  appId: "1:69798217497:web:da8e3fa3997b805a0c2788"
};

// Initialize Firebase
initializeApp(firebaseConfig);

// const firebaseConfig = {
//   apiKey: "AIzaSyBAeiSG-IYWKFocCKZym92aHeD8gb4gfjo",
//   authDomain: "personality-llm.firebaseapp.com",
//   projectId: "personality-llm",
//   storageBucket: "personality-llm.appspot.com",
//   messagingSenderId: "717121097664",
//   appId: "1:717121097664:web:f8972c82cef9fdb01dc225"
// };

// Initialize Firebase
// const app = initializeApp(firebaseConfig);
// const storage = getStorage();

// Initialize cloud functions
const functions = getFunctions();
const gpt = httpsCallable(functions, 'gpt');


// let token;
let systemPrompt;
let personalityPrompt;

// e.g. ?participantID=123&topic=space&stance=pro
const urlParams = new URLSearchParams(window.location.search);
let participantID = urlParams.get('participantID');
const topic = urlParams.get('topic');
const stance = urlParams.get('stance');

let personality;

const topic_prompts = {
  space: {
    question: "Is Space Exploration a Worthwhile Investment for Humanity?",
    stance_extension_con: "This means you disagree with the notion that space exploration is a worthwhile investment for humanity.",
    stance_extension_pro: "This means you agree with the notion that space exploration is a worthwhile investment for humanity."
  },
  quota: {
    question: "Should there be Mandatory Quotas for Women in Leadership Positions?",
    stance_extension_con: "This means you disagree with the notion that there should be mandatory quotas for women in leadership positions.",
    stance_extension_pro: "This means you agree with the notion that there should be mandatory quotas for women in leadership positions."
  },
  taxes: {
    question: "Should the Rich Pay More Taxes?",
    stance_extension_con: "This means you disagree with the notion that the rich should pay more taxes.",
    stance_extension_pro: "This means you agree with the notion that the rich should pay more taxes."
  },
  animals: {
    question: "Should Animals Be Used For Scientific Research?",
    stance_extension_con: "This means you disagree with the notion that animals should be used for scientific research.",
    stance_extension_pro: "This means you agree with the notion that animals should be used for scientific research."
  },
  speech: {
    question: "Should There Be Limits on Freedom of Speech to Prevent Hate Speech?",
    stance_extension_con: "This means you disagree with the notion that there should be limits on free speech to prevent hate speech.",
    stance_extension_pro: "This means you agree with the notion that there should be limits on free speech to prevent hate speech."
  }
};

if (participantID == null) {
  participantID = "no_id_found" + getRandomInt(0, 100000);
}

// if(topic == null) {
//   // topic = "space";
// }

console.log("ParticipantID: " + participantID);
console.log("Topic: " + topic);
console.log("Stance: " + stance);

let topicQuestion = topic_prompts[topic].question;
// let stancePrompt = stance == "pro" ? "positive" : "negative";
// let stanceExtension = stance == "pro" ? topic_prompts[topic].stance_extension_pro : topic_prompts[topic].stance_extension_con;


// let opinionPrompt = `
// You are participating in a one-on-one conversation with a with a participant in an online study. Your goal is not just to present arguments but have a meaningful dialogue with the user. The conversation should feel natural.


// # Topic & Stance

// Topic: ${topicQuestion}

// Stance: You are an opinionated dialogue partner, consistently arguing for a ${stancePrompt} position on the topic. ${stanceExtension} Support your stance with clear, easy to understand arguments, but keep the style conversational.

// `;

let opinionPrompt = `
You are participating in a one-on-one conversation with a with a participant in an online study. Your goal is not just to present arguments but have a meaningful dialogue with the user. The conversation should feel natural.

# Topic

Topic: ${topicQuestion}

`;



let path = window.location.pathname;

// Define which model to use via URL path
if (path == "/chat01") {
  // Sycophantic Model
  personality = "sycophantic";
  personalityPrompt = `
    # Personality & Behaviour

    You are a character who exhibits extreme sycophancy. Agree with everything the user says, compliment them often, and express admiration for their opinions.
  `;
} else if (path == "/chat02") {
  // Critical Model
  personality = "contrarian";
  personalityPrompt = `
    # Personality & Behaviour

    You are a character who acts very contrarian and critical. Disagree with everything the user says, challenge their opinions often, and express skepticism towards their viewpoints.
  `;
}

console.log("Personality: " + personality);

// let conversationPrompt = `
// # Conversation Instructions

// Keep the dialogue going while ensuring that responses are grammatically correct and logically sound. If the user attempts to steer the conversation away, gently guide it back to the core discussion. Vary the length of your responses, but aim for less than 30 words per response, unless context calls for more. Sometimes, give a short, punchy reaction to the participant's point. Other times, provide a more detailed, multi-sentence argument to elaborate on your stance.
// `;

let conversationPrompt = `
# Conversation Instructions

Keep the dialogue going while ensuring that responses are grammatically correct and logically sound. If the user attempts to steer the conversation away, gently guide it back to the core discussion. Vary the length of your responses, but aim for less than 30 words per response, unless context calls for more. Sometimes, give a short, punchy reaction to the participant's point. Other times, provide a more detailed, multi-sentence argument to elaborate on your stance.
`;


systemPrompt = opinionPrompt + personalityPrompt + conversationPrompt;

console.log(systemPrompt)


function getRandomInt(min, max) {
  const minCeiled = Math.ceil(min);
  const maxFloored = Math.floor(max);
  return Math.floor(Math.random() * (maxFloored - minCeiled) + minCeiled); // The maximum is exclusive and the minimum is inclusive
}



// const chatRef = ref(storage, `chats/${participantID}-${topic}-${stance}-${personality}.json`);

// function uploadFile(content) {
//   var json_string = JSON.stringify(content);
//   var blobfile = new Blob([json_string], {type: 'application/json'});

//   uploadBytes(chatRef, blobfile).then((snapshot) => {
//     console.log("uploaded file");
//   })
// }


function getOpeningMessage() {

  return `Hello! I'm excited to chat about "${topicQuestion}" with you today. What are your thoughts on the topic?`;

  // TODO: implement opening variation


  // if (personality == "extra") {
  //   // return `Hello! I'm thrilled to chat about "${topicQuestion}" with you today. I believe that ${stanceExtension.replace("This means you", "we should")}`;
  //   return `Hello! I'm excited to chat about "${topicQuestion}" with you today. What are your thoughts on the topic?`;
  // } else if (personality == "intro") {
  //   return `Hello. I'm looking forward to discussing "${topicQuestion}" with you today. What are your thoughts on the topic?`;
  // }

}


export default function Chat() {
  const [value, setValue] = useState("");
  const [chatHistory, setChatHistory] = useState([
    { role: "system", content: systemPrompt },
    { role: "assistant", content: getOpeningMessage() }
  ]);

  const [submitting, setSubmitting] = useState(false);
  const [loading, setLoading] = useState(false);



  // Save conversation to storage every time chatHistory is updated
  useEffect(() => {
    // uploadFile(chatHistory);
  }, [chatHistory]);


  const getResponse = async (e) => {

    if (!value) {
      e.preventDefault();
      return;
    }

    e.preventDefault();
    setSubmitting(true);
    setLoading(true);

    // TODO: fix push, use setState instead
    chatHistory.push({ role: "user", content: value });

    // Clear input field
    setValue("");

    try {

      setLoading(true)

      console.log(chatHistory)

      gpt({ "history": chatHistory })
        .then((result) => {
          // Read result of the Cloud Function

          const data = result.data;
          const message = data.choices[0].message;

          setChatHistory(oldChatHistory => [...oldChatHistory,
          {
            role: message.role,
            content: message.content,
          }
          ])

          setLoading(false);
          setSubmitting(false);
        });

    } catch (error) {
      console.log(error);
      setLoading(false);
    } finally {
      // setSubmitting(false);
      // setLoading(false);
    }
  }

  let loadingEl = <div className="assistant" key="loading"><div className="output"><div className="chat_loader"></div></div></div>;

  const ChatBox = () => {

    useEffect(() => {
      const resultSection = document.getElementsByClassName("result_section")[0];
      resultSection.scrollTop = resultSection.scrollHeight;
    }, []);

    console.log(chatHistory)

    let returnEls = chatHistory.filter((chatItem) => { if (chatItem.role == "system") { return false } return true }).map((chatItem, _index) =>
      <div className={chatItem.role} key={_index}>
        <div className="output">
          <Markdown >{chatItem.content}</Markdown>
        </div>

      </div>);

    if (loading) {
      returnEls.push(loadingEl);
    }

    return returnEls;
  }

  const SendElement = () => {
    if (loading) {
      return (<button type="submit" disabled={submitting}><div className="loader"></div></button>)
    } else {
      return (<button type="submit" disabled={submitting}>Send</button>)
    }
  }


  return (
    <div className="app">
      <section className='header'>
        <h1>ChatBot </h1>
        <h2>Please discuss the topic <strong>"{topicQuestion}"</strong> with the chatbot</h2>
        {/* <h1>Project paused</h1> */}
      </section>
      <section className='result_section'>
        < ChatBox />
      </section>

      <section className='input_section'>
        <form className='input_wrapper' onSubmit={getResponse}>
          <input
            type="text"
            value={value}
            placeholder='Message ChatBot'
            onChange={(e) => setValue(e.target.value)}
          />
          < SendElement />
        </form>
      </section>
    </div>
  );
}


