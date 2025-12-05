#!/bin/sh
set -e

# Hardened entrypoint for Chroma container.
# Responsibilities:
# - idempotently ensure persistent dirs are owned by the application user
# - verify those dirs are writable before dropping privileges
# - provide clear error messages if initialization fails

APP_UID=1000
APP_GID=1000
PERSIST_DIRS="/data /chroma /chroma/data"

echo "[entrypoint] ensuring persist directories exist and are writable"

for d in $PERSIST_DIRS; do
  if [ -d "$d" ]; then
    # Only chown if we find any file not owned by APP_UID (avoid unnecessary chown)
    if find "$d" -mindepth 1 -not -user "$APP_UID" -print -quit >/dev/null 2>&1; then
      echo "[entrypoint] fixing ownership of $d to ${APP_UID}:${APP_GID}"
      chown -R ${APP_UID}:${APP_GID} "$d" || {
        echo "[entrypoint][error] chown failed for $d" >&2
      }
    else
      echo "[entrypoint] ownership already correct for $d"
    fi

    # Verify writeability by creating a temp file
    testfile="$d/.chown_test_$$"
    if ! touch "$testfile" >/dev/null 2>&1; then
      echo "[entrypoint][error] $d is not writable by root or chown did not fix permissions" >&2
      echo "[entrypoint][hint] If this is a Docker named volume, run: docker run --rm -v chroma_data:/data alpine sh -c \"chown -R 1000:1000 /data\"" >&2
      exit 1
    else
      rm -f "$testfile" || true
    fi
  fi
done

# Exec as the application user (drops privileges). If gosu isn't available,
# fall back to running directly (best-effort).
if [ -x "/usr/local/bin/gosu" ]; then
  exec /usr/local/bin/gosu ${APP_UID}:${APP_GID} dumb-init -- chroma "$@"
else
  echo "[entrypoint][warn] gosu not found, running without dropping privileges"
  exec dumb-init -- chroma "$@"
fi
