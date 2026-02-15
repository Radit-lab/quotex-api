const http = require('http');

const server = http.createServer((req, res) => {
    res.writeHead(200, {'Content-Type': 'text/html'});
    res.end(`
        <h1>✅ Node.js is Working!</h1>
        <p>Node Version: ${process.version}</p>
        <p>Platform: ${process.platform}</p>
    `);
});

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
