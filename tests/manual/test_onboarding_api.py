import requests
import sys

def main():
    base_url = "http://127.0.0.1:8000"
    user_id = "user_test_123"

    print("Checking backend API root...")
    try:
        r = requests.get(f"{base_url}/")
        print(f"Root status: {r.status_code}")
        print(f"Root response: {r.json()}")
    except Exception as e:
        print(f"Failed to connect to backend: {e}")
        sys.exit(1)

    import uuid
    user_id = f"user_{uuid.uuid4().hex[:8]}"

    print(f"\nQuerying onboarding state for a brand-new user {user_id} (should auto-provision)...")
    r = requests.get(f"{base_url}/api/onboarding/state", headers={"X-User-Id": user_id})
    print(f"State status: {r.status_code}")
    print(f"State response: {r.json()}")

    print("\nUpdating onboarding identity...")
    identity_payload = {
        "first_name": "Test",
        "last_name": "User",
        "current_role_id": "backend_engineer",
        "current_role_title": "Backend Engineer",
        "years_in_role": 3.0,
        "career_level": "mid",
        "country": "Uzbekistan",
        "authorization": "authorized"
    }
    r = requests.post(f"{base_url}/api/onboarding/identity", json=identity_payload, headers={"X-User-Id": user_id})
    print(f"Identity update status: {r.status_code}")
    print(f"Identity update response: {r.json()}")

    print("\nUpdating onboarding goals...")
    goals_payload = {
        "goal_ids": ["remote", "better_salary"],
        "preferred_role_ids": ["backend_engineer", "ml_engineer"],
        "preferred_country_codes": ["DE", "NL"],
        "work_arrangements": ["remote", "hybrid"],
        "salary_min": 80000,
        "salary_max": 120000,
        "salary_currency": "EUR"
    }
    r = requests.post(f"{base_url}/api/onboarding/goals", json=goals_payload, headers={"X-User-Id": user_id})
    print(f"Goals update status: {r.status_code}")
    print(f"Goals update response: {r.json()}")

    print("\nQuerying onboarding state after updates...")
    r = requests.get(f"{base_url}/api/onboarding/state", headers={"X-User-Id": user_id})
    print(f"State status: {r.status_code}")
    print(f"State response: {r.json()}")

    # ─── Resume upload & extraction test ───
    print("\nCreating valid PDF resume file using PyMuPDF (fitz)...")
    import os
    import fitz
    os.makedirs("personal", exist_ok=True)
    mock_pdf_path = "personal/mock_resume.pdf"
    
    # Create valid PDF layout
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (50, 50),
        "Abdullokh Abdukodirov\n"
        "Senior Backend Engineer\n\n"
        "Skills: Python, Go, FastAPI, React, SQL, PostgreSQL, Docker, Git\n\n"
        "Experience:\n"
        "Google - Backend Engineer (2020-2023)\n"
        "- Designed and optimized backend services\n"
        "- Scaled database systems\n"
        "Facebook - Software Engineer (2018-2020)\n"
        "- Developed microservices using Python and Go\n"
    )
    doc.save(mock_pdf_path)
    doc.close()

    print("\nUploading PDF resume...")
    with open(mock_pdf_path, "rb") as f:
        r = requests.post(
            f"{base_url}/api/onboarding/resume",
            files={"file": ("mock_resume.pdf", f, "application/pdf")},
            headers={"X-User-Id": user_id}
        )
    print(f"Upload status: {r.status_code}")
    print(f"Upload response: {r.json()}")
    
    if r.status_code == 200:
        job_id = r.json()["job_id"]
        print(f"\nPolling extraction job {job_id} status...")
        import time
        for _ in range(15):
            status_res = requests.get(f"{base_url}/api/onboarding/resume/{job_id}/status", headers={"X-User-Id": user_id})
            status_data = status_res.json()
            print(f"Job status: {status_data['status']}, progress: {status_data['progress']}%")
            if status_data["status"] in ("completed", "failed"):
                break
            time.sleep(1)
            
        print("\nQuerying onboarding state after resume extraction...")
        r = requests.get(f"{base_url}/api/onboarding/state", headers={"X-User-Id": user_id})
        print(f"State status: {r.status_code}")
        print(f"State response: {r.json()}")

        # ─── Graph building test ───
        print("\nStarting Career Graph building...")
        r = requests.post(f"{base_url}/api/onboarding/build-graph", headers={"X-User-Id": user_id})
        print(f"Build graph status: {r.status_code}")
        print(f"Build graph response: {r.json()}")

        if r.status_code == 200:
            graph_job_id = r.json()["job_id"]
            print(f"\nPolling graph building job {graph_job_id} status...")
            for _ in range(15):
                status_res = requests.get(f"{base_url}/api/onboarding/build-graph/{graph_job_id}/status", headers={"X-User-Id": user_id})
                status_data = status_res.json()
                print(f"Graph job status: {status_data['status']}, progress: {status_data['progress']}%")
                if status_data["status"] in ("completed", "failed"):
                    break
                time.sleep(1)

            print("\nQuerying onboarding state after graph building...")
            r = requests.get(f"{base_url}/api/onboarding/state", headers={"X-User-Id": user_id})
            print(f"State status: {r.status_code}")
            print(f"State response: {r.json()}")

if __name__ == "__main__":
    main()
