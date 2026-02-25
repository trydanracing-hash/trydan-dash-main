// server.js
const express = require('express');
const path = require('path');
const app = express();

// 🔥 Use Render's dynamic port
const PORT = process.env.PORT || 3000;

// Serve static files from the 'public' directory
app.use(express.static(path.join(__dirname, 'public')));

// Serve index.html on root route
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(PORT, () => {
    console.log(`✓ Dashboard is live on port ${PORT}`);
});
