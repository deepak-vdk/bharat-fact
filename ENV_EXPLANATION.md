````markdown
# Environment Files Explanation

## Why Two Files?

### `.env.example` (Template - Safe for GitHub)
```env
GEMINI_API_KEY=your_api_key_here
````

* Shows which environment variables are required
* Safe to commit and push to GitHub
* Helps others set up the project
* Contains no sensitive information

### `.env` (Contains Real Secrets - Do Not Push to GitHub)

```env
GEMINI_API_KEY=YOUR_REAL_API_KEY_HERE
```

* Should never be committed to GitHub (protected by `.gitignore`)
* Contains your actual API key
* Accessible only to you
* Used by the application during runtime

## Workflow

1. **Developer (You):**

   * Maintain a `.env` file with the real API key
   * Create a `.env.example` template
   * Push only `.env.example` to GitHub

2. **Other Users:**

   * Clone the GitHub repository
   * Copy `.env.example` to `.env`
   * Add their own API key to `.env`
   * Run the application

## Security Best Practices

* Keep API keys private
* Allow others to use the project without exposing secrets
* Prevent accidental leakage of sensitive information
* Follow professional development standards
