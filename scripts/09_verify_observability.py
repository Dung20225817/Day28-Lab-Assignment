# scripts/09_verify_observability.py
import requests, os

# Load .env file manually
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
if os.path.exists(env_path):
    for line in open(env_path):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

def check_prometheus():
    resp = requests.get("http://localhost:9090/api/v1/query",
                        params={"query": 'http_requests_total{job="api-gateway"}'})
    data = resp.json()
    assert data["status"] == "success"
    print("Integration 9 OK: Prometheus metrics flowing")

def check_langsmith():
    key = os.environ.get("LANGCHAIN_API_KEY", "")
    if not key or key == "your_langsmith_api_key_here":
        print("SKIP: LangSmith API key not configured (set LANGCHAIN_API_KEY in .env)")
        return
    from langsmith import Client
    client = Client(api_key=key)
    runs = list(client.list_runs(project_name="lab28-platform", limit=1))
    assert len(runs) > 0
    print("Integration 10 OK: LangSmith traces visible")

check_prometheus()
check_langsmith()
