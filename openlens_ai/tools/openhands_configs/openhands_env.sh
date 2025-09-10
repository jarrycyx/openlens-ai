

export RUNTIME=local
export DEBUG=true
export SANBOX_USER_ID=3407
export SANDBOX_TIMEOUT=3600
export LOG_ALL_EVENTS=true
export DISABLE_COLOR=true
export PIP_BREAK_SYSTEM_PACKAGES=1
alias python="python3"
alias python3="python3"
alias python310="python3"
alias python3.10="python3"
alias pip3="pip"

echo "env.sh: Setup environment variables complete"
echo $SANBOX_USER_ID

export PATH=$PATH:/home/openhands/.local/bin