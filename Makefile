.PHONY: install run dev test stop clean logs

# Default values (override with: make request REPO=/other/path QUERY="your question")
REPO ?= /Users/chirag.chiranjib/razorpay/golang/ebpf-openapi/keploy
QUERY ?= What are the probes used in the repo?

# Install dependencies
install:
	python3 -m venv .venv
	.venv/bin/pip install -e .

# Run the server
run:
	.venv/bin/python -m repo_agent.server

# Run with auto-reload (dev mode)
dev:
	.venv/bin/uvicorn repo_agent.server:app --reload --port 8001

# Test the server
test:
	curl -sS http://localhost:8001/.well-known/agent.json | python3 -m json.tool

# Send a sample request
request:
	@echo "Repo: $(REPO)"
	@echo "Query: $(QUERY)"
	curl -sS -X POST http://localhost:8001/ \
		-H "Content-Type: application/json" \
		-d '{"jsonrpc":"2.0","method":"message/send","id":"1","params":{"message":{"messageId":"m1","role":"user","parts":[{"text":"$(QUERY) repo_path: $(REPO)"}]}}}'

# View logs
logs:
	@ls -t tmp/logs/*.log 2>/dev/null | head -4 | xargs -I {} sh -c 'echo "=== {} ===" && tail -20 {}'

# Stop the server
stop:
	@lsof -ti:8001 | xargs kill -9 2>/dev/null || true
	@echo "Server stopped"

# Clean logs
clean:
	rm -rf tmp/logs/*
	rm -rf __pycache__ repo_agent/__pycache__ repo_agent/utils/__pycache__

