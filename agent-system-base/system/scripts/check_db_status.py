import os
import sys
from pathlib import Path

# Add services to sys.path
_SERVICES_DIR = Path(__file__).resolve().parent.parent / "services"
sys.path.insert(0, str(_SERVICES_DIR))

import db
import project_service
import task_service

def check():
    print(f"DATABASE_URL set: {'Yes' if os.environ.get('DATABASE_URL') else 'No'}")
    
    try:
        with db.connect() as conn:
            print("Connected to database successfully.")
            
            # Check schema_version
            try:
                rows = conn.execute("SELECT * FROM schema_version").fetchall()
                print(f"Applied migrations: {len(rows)}")
                for r in rows:
                    print(f"  - {dict(r)['migration_name']}")
            except Exception as e:
                print(f"Error reading schema_version: {e}")
            
            # Check projects
            projects = project_service.list_projects()
            print(f"Total projects: {len(projects)}")
            for p in projects:
                print(f"  - [{p['id']}] {p['name']} ({p['slug']})")
                
            # Check tasks
            tasks = task_service.list_tasks()
            print(f"Total tasks: {len(tasks)}")
            
    except Exception as e:
        print(f"Database connection error: {e}")

if __name__ == "__main__":
    check()
