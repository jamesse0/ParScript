# Generic Python 3 sandbox image (DESIGN.md §6).
# Build once:  docker build -t parscript-sandbox backend/sandbox
# One `docker run` per submission; no container pool.

FROM python:3.12-slim

WORKDIR /sandbox

# pytest is only used by the "system_design" problem category (test_kind='pytest'),
# which runs `python pytest_harness.py` instead of the default CMD. I/O-pair
# submissions never import it.
RUN pip install --no-cache-dir pytest==8.3.4

# The runner harness + submitted code are written in per-run by
# services/sandbox_runner.py, so nothing to COPY at build time yet.

CMD ["python", "runner.py"]
