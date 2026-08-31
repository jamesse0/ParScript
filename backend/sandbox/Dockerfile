# Generic Python 3 sandbox image (DESIGN.md §6).
# Build once:  docker build -t parscript-sandbox backend/sandbox
# One `docker run` per submission; no container pool.

FROM python:3.12-slim

WORKDIR /sandbox

# stdlib only tonight. Add a pip install here if a seeded problem needs a dep.

# The runner harness + submitted code are written in per-run by
# services/sandbox_runner.py, so nothing to COPY at build time yet.

CMD ["python", "runner.py"]
