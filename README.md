# InternLog - Internship Log Tracking System

A secure, multi-user web application designed for students to document, track, and monitor their daily internship logs and program metrics. Built using Flask and vanilla SQLite3 queries to ensure strict adherence to relational database constraints.

## 🚀 Core Features
- **Authentication & Multi-User Isolation:** Secure registration and login operations with cross-user data masking.
- **Dynamic Metrics Dashboard:** Tracks internship logs dynamically against the total required days with progress calculations.
- **Full CRUD Support:** Users can seamlessly build, view, modify, and delete log entries under active session scoping.
- **Robust Input Handling:** Automated sanitation flows for cleaning white spaces and blocking primitive script behaviors.

## 🛠️ Built With
- **Backend:** Python / Flask
- **Database:** SQLite3 (Raw SQL Only - No ORM)
- **Frontend:** Semantic HTML5 / Responsive CSS3 (Custom Theme Architecture)

## 📦 Local Setup Instructions

1. Clone the repository to your local directory:
   ```bash
   git clone <your-repository-url>
   cd InternLog
2. Initialize and trigger the virtual environment: 
   python -m venv venv
.\venv\Scripts\activate

3. Install required application dependencies:
   pip install -r requirements.txt

4. Build schema properties and initialize local tables:
   python create_db.py

5. Run the development deployment server:
   python app.py
  
  Open http://127.0.0.1:5000 inside your preferred standard browser.
 
 🧪 Unit Testing
Validate the internal business logic (data boundaries, verification flows, and metric calculations) using the embedded suite:

python -m unittest tests.py 
