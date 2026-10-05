#!/usr/bin/env bash
# Bootstrap pip + deps for arxiv-daily on scrp (no root needed)
set -e
export PATH="$HOME/.local/bin:$PATH"
curl -sSL https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
python3 /tmp/get-pip.py --user --quiet 2>&1 | tail -2 || true
python3 -m pip install --user --quiet pypdf requests 2>&1 | tail -2 || true
python3 -c 'import pypdf, requests; print("deps-ok", pypdf.__version__, requests.__version__)'
