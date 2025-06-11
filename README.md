----------------------------------------------------------------------------------------------------------------------------
CHIRP!

Tired of Twitter and Facebook? Try Chirp!

----------------------------------------------------------------------------------------------------------------------------
FEATURES:
----------------------------------------------------------------------------------------------------------------------------
User Authentication: Register, log in, and manage secure sessions.

O-Auth - Sign in with Microsoft or Google!

Real-Time Messaging: Send and receive messages instantly using WebSockets (via Flask-SocketIO).

Typing Indicators: See when someone is typing.

Chirp/Post to your feed and interact with other users Chirp

Account privacy settings

Delete account feature 

Read Receipts: Know when your messages have been read.

Message Notifications: Receive in-app notifications for new messages.

Responsive UI: Clean and functional interface for desktop and mobile.

----------------------------------------------------------------------------------------------------------------------------
TECHNOLOGIES USED
----------------------------------------------------------------------------------------------------------------------------
Flask (Python web framework)

Flask-SocketIO (WebSocket support)

POSTGRES SQL

AWS Cloud-Storage

SQLAlchemy (ORM for database operations)

Flask-Login (User authentication)

Flask-WTF (Form validation and CSRF protection)

HTML, CSS, JavaScript (Frontend)

----------------------------------------------------------------------------------------------------------------------------
GETTING STARTED
----------------------------------------------------------------------------------------------------------------------------
1. Clone the Repository
git clone https://github.com/your-username/chirp.git
cd chirp

2. Create and Activate a Virtual Environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

3. Install Dependencies
pip install -r requirements.txt

4. Set Up the Database
You can use SQLite for development:
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
Make sure your database URI is correctly configured in config.py.

5. Run the App
cmd - flask run OR python run.py
Then visit: http://localhost:5000
