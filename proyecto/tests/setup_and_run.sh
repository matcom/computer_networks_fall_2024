#!/bin/bash

if [[ -z "${PROTOCOL}" ]]; then
  echo "PROTOCOL environment variable is not set"
  exit 1
fi

if [[ ! "${PROTOCOL}" =~ ^[1-4]$ ]]; then
  echo "Invalid value for PROTOCOL environment variable: ${PROTOCOL}. Must be 1, 2, 3 or 4"
  exit 1
fi

dir_names=("http" "ftp" "smtp" "irc")
dir_index=$((PROTOCOL - 1))
tests_dir="tests/${dir_names[$dir_index]}"
setup_sh="${tests_dir}/install.sh"
test_sh="${tests_dir}/run.sh"

echo "Executing install.sh script: ${setup_sh}"
${setup_sh}

if [[ $? -ne 0 ]]; then
  echo "Test setup failed"
  exit 1
fi

echo "Setup succeeded"

echo "Executing run.sh script: ${test_sh}"
${test_sh}

if [[ $? -ne 0 ]]; then
  echo "Test execution failed"
  exit 1
fi

echo "Tests execution completed"