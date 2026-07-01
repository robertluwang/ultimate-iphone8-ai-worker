const express = require('express');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

// Configs for LiteLLM Gateway
const LITELLM_URL = process.env.LITELLM_URL || 'http://localhost:4000/v1/chat/completions';
const LITELLM_MASTER_KEY = process.env.LITELLM_MASTER_KEY || '';
const LITELLM_MODEL = process.env.LITELLM_MODEL || 'gemini-flash';

app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// API endpoint to proxy to LiteLLM Gateway
app.post('/api/chat', async (req, res) => {
    try {
        const { messages } = req.body;
        if (!messages || !Array.isArray(messages)) {
            return res.status(400).json({ error: 'Messages array is required.' });
        }

        const payload = {
            model: LITELLM_MODEL,
            messages: messages,
            temperature: 0.3
        };

        const headers = {
            'Content-Type': 'application/json'
        };

        if (LITELLM_MASTER_KEY) {
            headers['Authorization'] = `Bearer ${LITELLM_MASTER_KEY}`;
        }

        const response = await fetch(LITELLM_URL, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error(`LiteLLM Gateway error: ${response.status} - ${errorText}`);
            return res.status(response.status).json({ error: `Gateway returned status ${response.status}` });
        }

        const data = await response.json();
        return res.json(data);
    } catch (err) {
        console.error('Error communicating with LiteLLM Gateway:', err);
        return res.status(500).json({ error: 'Internal server error or gateway offline. Please check if your SSH tunnel is active.' });
    }
});

app.listen(PORT, '0.0.0.0', () => {
    console.log(`🚀 Chatbot Web Server running at http://localhost:${PORT}`);
    console.log(`🌐 Proxying requests to LiteLLM at: ${LITELLM_URL}`);
    console.log(`🤖 Using model: ${LITELLM_MODEL}`);
});
