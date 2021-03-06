#!/bin/bash

# Common settings
export SERVER_URL='127.0.0.1'
export SERVER_PORT='4181'

# First agent
export AGENT_CLS_PATH='agent.chaotic.ChaoticAgent'
export AGENT_NAME='Chaotic'
pipenv run python client.py &
A1_PID=$!
echo "First agent pid:"$A1_PID

# Second agent
export AGENT_CLS_PATH='agent.dummy.DummyAgent'
export AGENT_NAME='Dummy'
pipenv run python client.py &
A2_PID=$!
echo "First agent pid:"$A2_PID

# Third agent
export AGENT_CLS_PATH='agent.cheater.CheaterAgent'
export AGENT_NAME='Cheater'
pipenv run python client.py &
A3_PID=$!
echo "First agent pid:"$A3_PID

# Fourth agent
export AGENT_CLS_PATH='agent.fair.FairAgent'
export AGENT_NAME='Fair'
pipenv run python client.py &
A4_PID=$!
echo "First agent pid:"$A4_PID

# Game server
export TOTAL_OFFER=100
export TOTAL_ROUNDS=5000
export CLIENTS_AMOUNT=4
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
kill_if_exists $A3_PID
kill_if_exists $A4_PID
