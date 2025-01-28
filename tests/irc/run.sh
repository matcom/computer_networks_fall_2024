 --user test --body test

echo "Executing run.sh script:"

status=0

# Test 1: Conectar, establecer y cambiar nickname
echo "Running Test 1: Conectar, establecer y cambiar nickname"
./run.sh -H "localhost" -p "8080" -n "TestUser1" -c "/nick" -a "NuevoNick"
if [[ $? -ne 0 ]]; then
  echo "Test 1 failed"
  status=1
fi

# Test 2: Entrar a un canal
echo "Running Test 2: Entrar a un canal"
./run.sh -H "localhost" -p "8080" -n "TestUser1" -c "/join" -a "#Nuevo"
if [[ $? -ne 0 ]]; then
  echo "Test 2 failed"
  status=1
fi

# Test 3: Enviar un mensaje a un canal
echo "Running Test 3: Enviar un mensaje a un canal"
${test_sh} -H "localhost" -p "8080" -n "TestUser1" -c "/msg" -a "#General Hello, world!"
if [[ $? -ne 0 ]]; then
  echo "Test 3 failed"
  status=1
fi

# Test 4: Salir de un canal
echo "Running Test 4: Salir de un canal"
./run.sh -H "localhost" -p "8080" -n "NewNick" -c "/part" -a "#General"
if [[ $? -ne 0 ]]; then
  echo "Test 4 failed"
  status=1
fi

# Test 5: Desconectar del servidor
echo "Running Test 5: Desconectar del servidor"
./run.sh -H "localhost" -p "8080" -n "NewNick" -c "/quit" -a "Goodbye!"
if [[ $? -ne 0 ]]; then
  echo "Test 5 failed"
  status=1
fi

if [[ $status -ne 0 ]]; then
  echo "Tests failed"
  exit 1
fi

echo "All custom tests completed successfully"

echo "Tests execution completed"