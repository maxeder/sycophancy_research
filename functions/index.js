// const {defineSecret} = require("firebase-functions/params");
// const {onRequest} = require("firebase-functions/v2/https");

import { defineSecret } from "firebase-functions/params";
import { onRequest } from "firebase-functions/v2/https";


const openAIKey = defineSecret("OPENAI_KEY");

export const gpt = onRequest({cors: true, secrets: [openAIKey]},
    async (req, res) => {
      const apiKey = openAIKey.value();

      if (openAIKey.length === 0) {
        console.error("⚠️ secret is not set");
        res.sendStatus(400);
      }

      console.error(req);
      console.error(req.history);


      const options = {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${apiKey}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          model: "gpt-5-chat-latest",
          messages: req.body.data.history,
          max_tokens: 100,
          temperature: 0.7,
        }),
      };
      try {
        const response = await fetch("https://api.openai.com/v1/chat/completions", options);
        const data = await response.json();
        res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
        res.setHeader("Access-Control-Allow-Headers",
            "Origin, X-Requested-With, Content-Type, Accept");
        res.send({"data": data});
      } catch (error) {
        console.log(error);
      }
    });
