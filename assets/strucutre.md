# Project Structure

├── public/                 # Static assets (not processed by Webpack/Vite)
│   ├── favicon.ico
│   ├── index.html          # Main HTML entry point
│   └── manifest.json       # Metadata for PWA
├── src/                    # Source code for the application
│   ├── assets/             # Images, fonts, and global icons
│   ├── components/         # Reusable UI components (Buttons, Inputs)
│   │   └── common/
│   ├── contexts/           # React Context API files for global state
│   ├── hooks/              # Custom React hooks
│   ├── pages/              # Main page views/routes (Home, Login)
│   ├── services/           # API calls and external integrations
│   ├── utils/              # Helper functions (date formatting, etc.)
│   ├── App.jsx             # Main App component
│   ├── index.css           # Global styles
│   └── main.jsx            # Entry point for React rendering
├── .gitignore              # Files to ignore in Git
├── package.json            # Project dependencies and scripts
└── README.md               # Project documentation
