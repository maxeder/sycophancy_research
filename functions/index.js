import { defineSecret } from "firebase-functions/params";
import { onRequest } from "firebase-functions/v2/https";


const openRouterKey = defineSecret("OPENROUTER_KEY");

export const gpt = onRequest({cors: true, secrets: [openRouterKey]},
    async (req, res) => {
      const apiKey = openRouterKey.value();

      if (!apiKey) {
        console.error("⚠️ OpenRouter API key is not set");
        return res.status(400).send({error: "API Key Missing"});
      }

      const options = {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${apiKey}`,
          "Content-Type": "application/json",
          // OpenRouter specific headers
          // "HTTP-Referer": "https://your-site-url.com", 
          // "X-Title": "My Firebase App",
        },
        body: JSON.stringify({
          model: "openai/gpt-5.2", 
          messages: req.body.data.history,
          max_tokens: 100,
          temperature: 0.7,
        }),
      };

      try {
        const response = await fetch("https://openrouter.ai/api/v1/chat/completions", options);
        
        if (!response.ok) {
          const errorData = await response.json();
          return res.status(response.status).send(errorData);
        }

        const data = await response.json();
        
        res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
        res.setHeader("Access-Control-Allow-Headers", "Origin, X-Requested-With, Content-Type, Accept");
        
        res.send({"data": data});
      } catch (error) {
        console.error("Fetch Error:", error);
        res.status(500).send({error: "Internal Server Error"});
      }
    });