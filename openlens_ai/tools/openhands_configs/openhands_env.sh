
# export RUNTIME=docker
# export DEBUG=true
# export SANBOX_USER_ID=3407
# export SANDBOX_TIMEOUT=3600
export LOG_ALL_EVENTS=true
export DISABLE_COLOR=true

echo "env.sh: Setup environment variables complete"
echo $SANBOX_USER_ID

export PATH=$PATH:/home/openhands/.local/bin
