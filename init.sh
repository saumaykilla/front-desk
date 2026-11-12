#!/usr/bin/env bash

set -Eeuo pipefail

# Front Desk Agent - Development Environment Initialization

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

BACKEND_DIR="$ROOT_DIR/backend"
VOICE_DIR="$ROOT_DIR/voice-agent"
WEB_DIR="$ROOT_DIR/web"

log() {
    printf "\n[init] %s\n" "$1"
}

warn() {
    printf "\n[warning] %s\n" "$1"
}

fail() {
    printf "\n[error] %s\n" "$1" >&2
    exit 1
}

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

log "Checking development prerequisites..."

command_exists python3 || fail "Python 3 is required."
command_exists node || fail "Node.js is required."
command_exists npm || fail "npm is required."

python3 --version
node --version
npm --version

log "Checking project directories..."

for dir in "$BACKEND_DIR" "$VOICE_DIR" "$WEB_DIR"; do
    if [[ ! -d "$dir" ]]; then
        warn "Directory not found: ${dir#$ROOT_DIR/}"
    fi
done

setup_python_environment() {
    local project_dir="$1"
    local project_name="$2"

    if [[ ! -d "$project_dir" ]]; then
        warn "Skipping $project_name: directory does not exist."
        return
    fi

    local requirements_file="$project_dir/requirements.txt"
    local venv_dir="$project_dir/.venv"

    log "Setting up $project_name Python environment..."

    if [[ ! -d "$venv_dir" ]]; then
        python3 -m venv "$venv_dir"
        log "Created virtual environment: ${venv_dir#$ROOT_DIR/}"
    else
        log "Virtual environment already exists."
    fi

    if [[ -f "$requirements_file" ]]; then
        "$venv_dir/bin/python" -m pip install --upgrade pip
        "$venv_dir/bin/python" -m pip install -r "$requirements_file"
    else
        warn "No requirements.txt found for $project_name. Skipping dependency installation."
    fi
}

setup_web_environment() {
    if [[ ! -d "$WEB_DIR" ]]; then
        warn "Skipping web setup: directory does not exist."
        return
    fi

    if [[ ! -f "$WEB_DIR/package.json" ]]; then
        warn "No package.json found in web/. Skipping npm installation."
        return
    fi

    log "Installing web dependencies..."

    if [[ -f "$WEB_DIR/package-lock.json" ]]; then
        (cd "$WEB_DIR" && npm ci)
    else
        (cd "$WEB_DIR" && npm install)
    fi
}

setup_python_environment "$BACKEND_DIR" "Backend"
setup_python_environment "$VOICE_DIR" "Voice Agent"
setup_web_environment

log "Initialization complete."

printf "\nNext steps:\n"
printf "  Backend:     cd backend && source .venv/bin/activate\n"
printf "  Voice agent: cd voice-agent && source .venv/bin/activate\n"
printf "  Web:         cd web && npm run dev\n"
printf "\nRun the project's documented verification commands before considering setup complete.\n"