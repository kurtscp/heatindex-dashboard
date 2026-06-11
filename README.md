# HeatWatch - Metro Manila Heat Index Dashboard

HeatWatch is a Flask-based web application designed to analyze, visualize, and predict historical heat index patterns for Metro Manila.

## 🚀 How to Run Locally

If you are cloning this repository to run on your own machine, please follow the setup steps below carefully.

### 1. Prerequisites
Ensure you have the following installed on your machine:
- **Python 3.8+**
- **Git**

### 2. Setup Instructions

1. **Clone the repository:**
   Open your terminal (or Command Prompt / PowerShell) and run:
   ```bash
   git clone <your-github-repo-link-here>
   cd "HEATINDEX DASHBOARD"
   ```

2. **Create a Virtual Environment (Recommended):**
   This prevents dependency conflicts with other Python projects.
   ```bash
   python -m venv venv
   ```

3. **Activate the Virtual Environment:**
   - On **Windows**:
     ```powershell
     venv\Scripts\activate
     ```
   - On **Mac/Linux**:
     ```bash
     source venv/bin/activate
     ```

4. **Install Required Packages:**
   Install all the necessary libraries like Flask, Pandas, and Scikit-Learn:
   ```bash
   pip install -r requirements.txt
   ```

### 3. Running the Application

Because of the project's folder structure, you **must run the app from the root directory**, pointing Python to the entry file inside the `main` folder.

Run the following command:
```bash
python main/app.py
```

### 4. Usage
1. Open your web browser and go to: `http://127.0.0.1:5000/`
2. You will be greeted by the upload page.
3. Click the upload area and select the default dataset provided in this repository located at:
   `rawData/raw_manila_heatindex_2015_2026.csv`
4. Click **Proceed to Dashboard** to view the analytics!

## 📁 Project Structure
- `main/` - Contains the `app.py` Flask entrypoint.
- `frontend/` - Contains all HTML templates and static CSS/JS files.
- `backend/` - Contains the data preprocessing, analytics logic, and machine learning models.
- `rawData/` - Contains the default CSV datasets.
