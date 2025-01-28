#!/bin/bash

# Execute the test script with parameters
echo "Executing run.sh script:"

# Define the tests with descriptions and parameters
tests=(
  "Test 1: List files in the server"
  "-s 127.0.0.1 -p 2121 -u user1 -pw password1 -c ls"

  "Test 2: Change directory to 'docs'"
  "-s 127.0.0.1 -p 2121 -u user1 -pw password1 -c cd -a docs"

  "Test 3: Print current working directory"
  "-s 127.0.0.1 -p 2121 -u user1 -pw password1 -c pwd"

  "Test 4: Create a new directory named 'new_folder'"
  "-s 127.0.0.1 -p 2121 -u user1 -pw password1 -c mkdir -a new_folder"

  "Test 5: Remove directory named 'old_folder'"
  "-s 127.0.0.1 -p 2121 -u user1 -pw password1 -c rd -a old_folder"

  "Test 6: Remove file named 'file.txt'"
  "-s 127.0.0.1 -p 2121 -u user1 -pw password1 -c rf -a file.txt"

  "Test 7: Rename file from 'old_name.txt' to 'new_name.txt'"
  "-s 127.0.0.1 -p 2121 -u user1 -pw password1 -c rename -a old_name.txt new_name.txt"

  "Test 8: Download file 'file_to_download.txt'"
  "-s 127.0.0.1 -p 2121 -u user1 -pw password1 -c dow -a file_to_download.txt"

  "Test 9: Upload file 'file_to_upload.txt'"
  "-s 127.0.0.1 -p 2121 -u user1 -pw password1 -c upl -a file_to_upload.txt"

  "Test 10: Quit the server"
  "-s 127.0.0.1 -p 2121 -u user1 -pw password1 -c quit"
)

for ((i = 0; i < ${#tests[@]}; i += 2)); do
  description="${tests[$i]}"
  params="${tests[$i + 1]}"

  echo "Running ${description}"
  echo "Parameters: ${params}"
  ./run.sh ${params}

  if [[ $? -ne 0 ]]; then
    echo "Test failed: ${description}"
    exit 1
  fi

  echo "Test passed: ${description}"
  echo "----------------------------------------"
done

echo "All tests execution completed"