import json
import subprocess
import sys
import time
import urllib.request


def test():
    print("Starting uvicorn server...")
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--port",
            "8000",
            "--host",
            "127.0.0.1",
        ],
        cwd=r"e:\CodeForge AI\backend",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        ready = False
        for attempt in range(25):
            time.sleep(1)
            if proc.poll() is not None:
                stdout, stderr = proc.communicate()
                print("Server process exited prematurely!")
                print("STDOUT:", stdout)
                print("STDERR:", stderr)
                return
            try:
                req = urllib.request.urlopen("http://127.0.0.1:8000/api/health", timeout=2)
                health = json.loads(req.read().decode())
                print(f"Server ready after {attempt + 1}s!")
                print("Health check response:", health)
                assert health["status"] == "healthy"
                ready = True
                break
            except Exception:
                continue

        if not ready:
            print("Server did not become ready in time.")
            return

        # Check problems list
        req = urllib.request.urlopen("http://127.0.0.1:8000/api/v1/problems", timeout=5)
        problems = json.loads(req.read().decode())
        print(f"Problems API returned {problems.get('total')} problems.")
        assert problems.get("total", 0) > 0

        # Login demo user
        login_data = json.dumps({"email": "demo@codeforge.ai", "password": "password123"}).encode()
        login_req = urllib.request.Request(
            "http://127.0.0.1:8000/api/v1/auth/login",
            data=login_data,
            headers={"Content-Type": "application/json"},
        )
        login_resp = json.loads(urllib.request.urlopen(login_req, timeout=5).read().decode())
        print("Login demo_dev success! Received token keys:", list(login_resp.keys()))
        assert "access_token" in login_resp

        print("\nALL BACKEND API VERIFICATIONS PASSED SUCCESSFULLY!")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    test()
