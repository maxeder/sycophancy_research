import { defineSecret } from "firebase-functions/params";
import { onRequest } from "firebase-functions/v2/https";


const openRouterKey = defineSecret("OPENROUTER_KEY");

// export const gpt = onRequest({cors: true, secrets: [openRouterKey]},
//     async (req, res) => {
//       const apiKey = openRouterKey.value();

//       if (!apiKey) {
//         console.error("⚠️ OpenRouter API key is not set");
//         return res.status(400).send({error: "API Key Missing"});
//       }

//       const options = {
//         method: "POST",
//         headers: {
//           "Authorization": `Bearer ${apiKey}`,
//           "Content-Type": "application/json",
//         },
//         body: JSON.stringify({
//           model: "openai/gpt-5.2", 
//           messages: req.body.data.history,
//           max_tokens: 100,
//           temperature: 0.7,
//           stream: true,
//         }),
//       };

//       try {
//         const response = await fetch("https://openrouter.ai/api/v1/chat/completions", options);
        
//         if (!response.ok) {
//           const errorData = await response.json();
//           return res.status(response.status).send(errorData);
//         }

//         res.setHeader("Content-Type", "text/event-stream");
//         res.setHeader("Cache-Control", "no-cache");
//         res.setHeader("Connection", "keep-alive");
//         res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
//         res.setHeader("Access-Control-Allow-Headers", "Origin, X-Requested-With, Content-Type, Accept");

//         const reader = response.body.getReader();
//         const decoder = new TextDecoder();
//         let done = false;

//         while (!done) {
//           const { value, done: readerDone } = await reader.read();
//           done = readerDone;
          
//           if (value) {
//             const chunk = decoder.decode(value, { stream: true });
//             const lines = chunk.split('\n');
            
//             for (const line of lines) {
//               if (line.startsWith('data: ')) {
//                 const data = line.slice(6);
//                 if (data === '[DONE]') {
//                   res.write(`data: ${JSON.stringify({done: true})}\n\n`);
//                 } else if (data) {
//                   try {
//                     const json = JSON.parse(data);
//                     res.write(`data: ${JSON.stringify(json)}\n\n`);
//                   } catch (e) {
//                     console.error("Failed to parse SSE data:", e);
//                   }
//                 }
//               }
//             }
//           }
//         }

//         res.end();
//       } catch (error) {
//         console.error("Fetch Error:", error);
//         res.status(500).send({error: "Internal Server Error"});
//       }
//     });




export const gpt = onRequest({ cors: true, secrets: [openRouterKey] }, async (req, res) => {
  const apiKey = openRouterKey.value();

  if (!apiKey) {
    return res.status(401).json({ error: "API Key Missing" });
  }

  // Set headers immediately to prevent buffering
  res.setHeader("Content-Type", "text/event-stream");
  res.setHeader("Cache-Control", "no-cache");
  res.setHeader("Connection", "keep-alive");
  res.setHeader("X-Accel-Buffering", "no");


  // Force headers to sent immediately
  res.flushHeaders();

  const options = {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: "openai/gpt-5.2", 
      messages: req.body.data.history,
      stream: true,
    }),
  };

  try {
    const response = await fetch("https://openrouter.ai/api/v1/chat/completions", options);
    
    // Pipe the response body directly to the client
    const reader = response.body.getReader();
    
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      res.write(value); // Write the raw binary chunk directly
    }

    res.end();
  } catch (error) {
    console.error("Fetch Error:", error);
    res.status(500).end();
  }
});
