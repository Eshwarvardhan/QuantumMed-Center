# QuantumMed Center

![QuantumMed Center](static/images/hos.jpg)

A simple Flask-based hospital management website with the following features:

- User registration and login (Flask-Login)
- Patient records (add/list)
- Appointment scheduling
- Emergency SOS page showing nearby hospitals with a "send location" button (uses Geolocation API)
- AI assistant powered by OpenAI (optional)
- Voice recognition & text-to-speech for the AI chat (Web Speech API)

## Setup

1. **Clone repository**
   ```bash
   git clone <your-repo-url>
   cd Hospital_Management
   ```

2. **Create virtual environment & install dependencies**
   ```bash
   python -m venv venv
   venv\Scripts\activate    # Windows
   pip install -r requirements.txt
   ```

3. **Environment variables** (optional but recommended)
   ```powershell
   $env:SECRET_KEY="your-secret"
   $env:OPENAI_API_KEY="sk-..."   # required for AI brain
   $env:OPENAI_MODEL="gpt-4o-mini" # optional
   ```

4. **Run the application**
   ```bash
   python app.py
   ```
   Visit http://127.0.0.1:5000 in your browser.

## Using the App

- Register a new user and log in (you can now use either username or email to authenticate). Each user will be given a unique `client_id` automatically for API use.
- Go to **Patients**: add a patient record.
- Go to **Appointments**: schedule an appointment by selecting the patient name and entering date/time (slot conflict warning shown if time is taken).
- **SOS** page lists example hospitals; clicking "Send My Location" will prompt for geolocation and simulate sending it.
- **AI Assistant**: type a query or click the microphone button to speak input. The response is generated using OpenAI API key and can be read aloud with browser voice output.

## Deployment

- If you already have an existing `hospital.db` from before the email/client_id fields were added, delete or recreate it so the new columns are included. The application will also attempt to alter your table automatically on startup, but if you encounter an `OperationalError` you may need to remove the old database:
  ```bash
  rm hospital.db      # or delete manually on Windows
  ```
- Push code to a GitHub repository.
- Use a platform like [Heroku](https://www.heroku.com/), [PythonAnywhere](https://www.pythonanywhere.com/), or deploy via Docker on any server.
- Configure environment variables (SECRET_KEY, OPENAI_API_KEY) on the host.

Example Heroku steps:

```bash
heroku create
heroku config:set SECRET_KEY="mysecret" OPENAI_API_KEY="sk-..."
git push heroku main
heroku ps:scale web=1
``` 

You can also host just the frontend on GitHub Pages but backend requires a Python host.

## Notes

- This is a beginner-friendly project; feel free to expand with user roles, validations, map integration, SMS notifications, etc.
- The AI feature requires an OpenAI API key; without it the UI will display a warning.
- Voice functionality depends on modern browsers supporting the Web Speech API.

- **Custom background:**
  1. Copy or save your desired image file to `static/images/` within the project folder.
  2. Name it `bg.jpg` (or `bg.png`), or edit the `background` rule in `templates/base.html` to use your filename (e.g. `hospital.jpg`).
  3. Make sure the image resolution is large (at least 1920×1080) to avoid blurring.
  4. Reload the browser after replacing the file.


---

Happy hacking! 🚑
