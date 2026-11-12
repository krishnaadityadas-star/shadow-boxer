
#!/usr/bin/env bash
cd "$(dirname "$0")"

if [ -x ".venv/bin/python" ]; then
    PYTHON=".venv/bin/python"
elif [ -x "shadowboxer-env/bin/python" ]; then
    PYTHON="shadowboxer-env/bin/python"
else
    PYTHON="python3"
fi

exec "$PYTHON" shadow_boxer_mvp.py "$@"
