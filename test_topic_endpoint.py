"""Manual smoke check: python test_topic_endpoint.py (requires a running server)."""
import httpx


def main():
    response = httpx.post("http://127.0.0.1:8000/api/topic/discover",
                          json={"query": "test"}, timeout=10)
    print("Status:", response.status_code)
    print("Request ID:", response.headers.get("X-Request-ID"))
    print("Response:", response.text)
    response.raise_for_status()


if __name__ == "__main__":
    main()
