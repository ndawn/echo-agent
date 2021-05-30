#!/bin/sh

arq echo_agent.discover.cron.WorkerSettings > arq.log &

arq_pid="$!"

stop_arq () {
  kill $arq_pid
}

trap stop_arq EXIT

uvicorn echo_agent.app:app --port "$(python -c "from echo_agent.config import Config; config = Config(); print(config.agent_port, end='')")"
