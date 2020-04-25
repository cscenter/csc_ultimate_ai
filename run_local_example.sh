#!/bin/bash
set -e

# Common settings
export SERVER_URL='127.0.0.1'
export SERVER_PORT='4181'

# First agent
export AGENT_CLS_PATH='agent.chaotic.ChaoticAgent'
pipenv run python client.py &
A1_PID=$!
echo "First agent pid:"$A1_PID

# Second agent
export AGENT_CLS_PATH='agent.chaotic.ChaoticAgent'
pipenv run python client.py &
A2_PID=$!
echo "First agent pid:"$A2_PID

# Game server
export TOTAL_OFFER=100
export TOTAL_ROUNDS=100
export CLIENTS_AMOUNT=2
export RESPONSE_TIMEOUT=2
pipenv run python server.py

# Use kill for uncompleted agents
kill_if_exists () {
  if ps -p $1 > /dev/null
  then
      echo "$1 is alive, kill it"
      kill $1
  else
      echo "$1 is dead, ok"
  fi
}
kill_if_exists $A1_PID
kill_if_exists $A2_PID
