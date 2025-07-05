$htmlContent = @"
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StreamMate AI - Your Ultimate Streaming Companion</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 40px auto;
            padding: 0 20px;
            background-color: #f4f4f4;
            text-align: center;
        }
        .container {
            background-color: #fff;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #1a1a1a;
        }
        p {
            font-size: 1.1em;
            color: #555;
        }
        .download-button {
            display: inline-block;
            background-color: #007bff;
            color: #fff;
            padding: 15px 30px;
            text-decoration: none;
            font-size: 1.2em;
            font-weight: bold;
            border-radius: 5px;
            margin-top: 20px;
            transition: background-color 0.3s ease;
        }
        .download-button:hover {
            background-color: #0056b3;
        }
        .footer {
            margin-top: 40px;
            font-size: 0.9em;
            color: #777;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Welcome to StreamMate AI</h1>
        <p>The ultimate AI-powered assistant designed to revolutionize your live streaming experience. Engage with your audience like never before!</p>
        
        <a href="#" class="download-button">Download Latest Version (v1.0.11)</a>
        
        <div class="footer">
            <p>&copy; 2024 StreamMate AI. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"@

$htmlContent | Out-File -FilePath "index.html" -Encoding utf8 