import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.db.connection import db
from sqlalchemy import text

def main():
    print("Connecting to DB...")
    session = db.get_session()
    
    print("\n1. Active queries in pg_stat_activity:")
    try:
        sql = """
        SELECT pid, query, state, age(clock_timestamp(), query_start) 
        FROM pg_stat_activity 
        WHERE state != 'idle' AND query NOT LIKE '%pg_stat_activity%'
        """
        rows = session.execute(text(sql)).all()
        for r in rows:
            print(f"PID: {r[0]}, Query: {r[1]}, State: {r[2]}, Age: {r[3]}")
    except Exception as e:
        print("Error checking activity:", e)
        
    print("\n2. Active locks in pg_locks:")
    try:
        sql = """
        SELECT t.relname, l.locktype, l.mode, l.granted, l.pid 
        FROM pg_locks l 
        JOIN pg_class t ON l.relation = t.oid 
        WHERE t.relname = 'users'
        """
        rows = session.execute(text(sql)).all()
        for r in rows:
            print(f"Table: {r[0]}, LockType: {r[1]}, Mode: {r[2]}, Granted: {r[3]}, PID: {r[4]}")
    except Exception as e:
        print("Error checking locks:", e)
        
    session.close()

if __name__ == "__main__":
    main()
