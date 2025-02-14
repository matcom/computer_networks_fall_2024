using System;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Text.RegularExpressions;
using System.Collections.Generic; // Necesario para List<string>

class Client
{
    Socket socket;
Socket data_socket;
Socket dataSocketListener;
string server;
int port;
bool active;
string user;
string password;
string path;

// Funciones auxiliares
void SendCommand(string command)
{
    byte[] commandBytes = Encoding.ASCII.GetBytes(command + "\r\n");
    socket.Send(commandBytes);
    Console.WriteLine("Enviado: " + command);
}

string ReceiveResponse()
{
    byte[] buffer = new byte[1024];
    int bytesReceived = socket.Receive(buffer);
    return Encoding.ASCII.GetString(buffer, 0, bytesReceived);
}

void SendData(Socket dataSocket, string filePath)
    {
        byte[] buffer = new byte[1024];
        using (FileStream fileStream = new FileStream(filePath, FileMode.Open, FileAccess.Read))
        {
            int bytesRead;
            while ((bytesRead = fileStream.Read(buffer, 0, buffer.Length)) > 0)
            {
                dataSocket.Send(buffer, bytesRead, SocketFlags.None);
            }
        }
    }

void Init(){
    server = "10.10.10.6";
    port = 21;
    active = true;
    user = string.Empty;
    password = string.Empty;
    path = "/";
}

void SetActiveMode(){
    // 1. Crear un socket para escuchar las conexiones de datos entrantes
    dataSocketListener = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
    IPEndPoint localEndPoint = new IPEndPoint(IPAddress.Any, 0); // Escucha en cualquier IP disponible y deja que el sistema operativo asigne un puerto
    dataSocketListener.Bind(localEndPoint);
    dataSocketListener.Listen(1); // Solo acepta una conexión

    active = true;

    // 2. Obtener la dirección IP y el puerto asignado
    IPEndPoint dataEndpoint = (IPEndPoint)dataSocketListener.LocalEndPoint;
    string ipAddress = GetLocalIPAddress(); // Método auxiliar para obtener la IP local
    int port = dataEndpoint.Port;

    // 3. Formatear el comando PORT
    Port(ipAddress, port);

    string GetLocalIPAddress(){
        Socket socket = new Socket(AddressFamily.InterNetwork, SocketType.Dgram, 0);
        socket.Connect("8.8.8.8", 65530);
        IPEndPoint endPoint = socket.LocalEndPoint as IPEndPoint;
        return endPoint.Address.ToString();
    }
}

void SetPassiveMode()
    {
        SendCommand("PASV");
        string response = ReceiveResponse();
        Console.WriteLine(response);

        active = false;

        int startIndex = response.IndexOf("(") + 1;
        int endIndex = response.IndexOf(")");
        string data = response.Substring(startIndex, endIndex - startIndex);

        string[] parts = data.Split(',');

        //if (parts.Length == 6){
            string ipAddress = $"{parts[0]}.{parts[1]}.{parts[2]}.{parts[3]}";
            int port = int.Parse(parts[4]) * 256 + int.Parse(parts[5]);

            // Crear el socket de datos y conectarse
            data_socket = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
            data_socket.Connect(ipAddress, port);

            Console.WriteLine($"Conectado al modo pasivo: {ipAddress}:{port}\n");
        //}
    }

string ReceiveData(Socket dataSocket)
    {
        StringBuilder sb = new StringBuilder();
        byte[] buffer = new byte[1024];
        int bytesRead;

        while ((bytesRead = dataSocket.Receive(buffer)) > 0)
        {
            sb.Append(Encoding.ASCII.GetString(buffer, 0, bytesRead));
        }

        return sb.ToString();
    }


//Funciones Principales
void Connect(string _user, string _password)
{
    socket = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
    socket.Connect(server, port);
    Console.WriteLine(ReceiveResponse()); //Recibe el mensaje de bienvenida

    user = _user;
    password = _password;

    SendCommand("USER " + user);
    Console.WriteLine(ReceiveResponse());

    SendCommand("PASS " + password);
    Console.WriteLine(ReceiveResponse());
}

//No disponible en FreeFTPd
void Reinitialize(){
    Init();

    SendCommand("REIN");
    Console.WriteLine(ReceiveResponse());
}

void Help(){
    SendCommand("HELP");
    Console.WriteLine(ReceiveResponse());
}

void ChangeWorkingDirectory(string directory)
{
    path = directory;

    SendCommand("CWD " + directory);
    Console.WriteLine(ReceiveResponse());
}

void ChangeDirectoryUP(string directory)
{
    path = path.Substring(0, path.LastIndexOf('/'));

    SendCommand("CDUP");
    Console.WriteLine(ReceiveResponse());
}

//No disponible en FreeFTPd
void StructureMount(string path)
    {
        SendCommand("SMNT " + path);
        Console.WriteLine(ReceiveResponse());
    }

void Port(string ipAddress, int _port)
{
    server = ipAddress;
    port = _port;

    string[] ipParts = ipAddress.Split('.');
    int p1 = port / 256;
    int p2 = port % 256;
    
    SendCommand($"PORT {ipParts[0]},{ipParts[1]},{ipParts[2]},{ipParts[3]},{p1},{p2}");
    Console.WriteLine(ReceiveResponse());
}

void SetTransferType(char type)
    {
        if(type != 'A' && type != 'I'){
            Console.WriteLine("Solo argumentos A, I");
        }
            
        SendCommand("TYPE " + type);
        Console.WriteLine(ReceiveResponse());
    }

//No disponible en FreeFTPd. Obsoleto en la mayoria de clientes y servidores FTP modernos
void SetFileStructure(char structure)
    {
        if(structure != 'F' && structure != 'R' && structure != 'P'){
            Console.WriteLine("Solo argumentos F, R, P");
        }

        SendCommand("STRU " + structure);
        Console.WriteLine(ReceiveResponse());
    }

//Solo disponible S en FreeFTPd
void SetTransferMode(char mode)
    {
        if(mode != 'S' && mode != 'C' && mode != 'B'){
            Console.WriteLine("Solo argumentos S, C, B");
        }

        SendCommand("MODE " + mode);
        Console.WriteLine(ReceiveResponse());
    }

void Nothing(){
    SendCommand("NOOP");
    Console.WriteLine(ReceiveResponse());
}

void Features(){
    SendCommand("FEAT");
    Console.WriteLine(ReceiveResponse());
}

void Close()
{
    SendCommand("QUIT");
    Console.WriteLine(ReceiveResponse());
    socket.Close();
}

//Por ahora solo funciona el pasivo
void UploadFile(string localFilePath, string remoteFileName)
    {
        if(active){
            SetActiveMode();

            data_socket = dataSocketListener.Accept();
            Console.WriteLine("Mode setted up\n");

            SendCommand("STOR " + remoteFileName);
            string response = ReceiveResponse();
            Console.WriteLine(response);

            SendData(data_socket, localFilePath); // Enviar datos a traves del dataSocket
            data_socket.Shutdown(SocketShutdown.Send); // Indica al servidor que no se enviarán más datos
            data_socket.Close();

            Console.WriteLine(ReceiveResponse()); //Recibe la respuesta final del servidor

            dataSocketListener.Close();  //Limpiar el listener para la proxima operacion, si es que la hay
        }
        else{
            SendCommand("STOR " + remoteFileName);
            string response = ReceiveResponse();
            Console.WriteLine(response);

            SendData(data_socket, localFilePath); // Enviar datos a traves del dataSocket
            data_socket.Close();

            SetPassiveMode();

            Console.WriteLine(ReceiveResponse()); //Recibe la respuesta final del servidor
        }

    }

void DownloadFile(string remoteFilePath, string localFilePath)
{
    SetPassiveMode();

    SendCommand($"RETR {remoteFilePath}");
    Console.WriteLine(ReceiveResponse());

    // 2. Recibir el archivo y guardarlo
    FileStream fileStream = new FileStream(localFilePath, FileMode.Create, FileAccess.Write);

    byte[] buffer = new byte[4096];
    int bytesRead = int.MaxValue;

    data_socket.ReceiveTimeout = 10000; // 10 segundos de timeout

    Console.WriteLine("Conexión de datos establecida. Iniciando descarga...");
    while (bytesRead > 0)
    {
        try
        {
            bytesRead = data_socket.Receive(buffer, buffer.Length, SocketFlags.None);
            fileStream.Write(buffer, 0, bytesRead);
        }
        catch (SocketException ex)
        {
            // Si ocurre una excepción de timeout, asumir que no hay más datos
            if (ex.SocketErrorCode == SocketError.TimedOut) break;
        }
    }
    Console.WriteLine($"Archivo descargado a {localFilePath}\n");
                
    // 3. Cerrar la conexión de datos (importante)
    fileStream.Close();
    data_socket.Shutdown(SocketShutdown.Both);
    data_socket.Close();

    // Console.WriteLine($"Transferencia completada: " + ReceiveResponse());
}

void AppendFile(string remoteFilePath, string localFilePath)
{
    SetPassiveMode();

    SendCommand($"APPE {remoteFilePath}");
    Console.WriteLine(ReceiveResponse());

    // 2. Recibir el archivo y guardarlo
    FileStream fileStream = new FileStream(localFilePath, FileMode.Append, FileAccess.Write);

    byte[] buffer = new byte[4096];
    int bytesRead = int.MaxValue;

    data_socket.ReceiveTimeout = 10000; // 10 segundos de timeout

    while (bytesRead > 0)
    {
        try
        {
            bytesRead = data_socket.Receive(buffer, buffer.Length, SocketFlags.None);
            fileStream.Write(buffer, 0, bytesRead);
        }
        catch (SocketException ex)
        {
            // Si ocurre una excepción de timeout, asumir que no hay más datos
            if (ex.SocketErrorCode == SocketError.TimedOut) break;
        }
    }
                
    // 3. Cerrar la conexión de datos (importante)
    fileStream.Close();
    data_socket.Shutdown(SocketShutdown.Both);
    data_socket.Close();

    // Console.WriteLine($"Transferencia completada: " + ReceiveResponse());
}
//Implemento el comando ACCT ?

void RenameFile(string oldName, string newName)
{
    // 1. Enviar el comando RNFR
    SendCommand("RNFR " + oldName);
    string rnfrResponse = ReceiveResponse();
    Console.WriteLine(rnfrResponse);

    // 2. Verificar la respuesta (esperar "350 File exists, ready for destination name")
    if (!rnfrResponse.StartsWith("350"))
    {
        Console.WriteLine("Error: El servidor no aceptó el comando RNFR.");
        return;
    }

    // 3. Enviar el comando RNTO
    SendCommand("RNTO " + newName);
    string rntoResponse = ReceiveResponse();
    Console.WriteLine(rntoResponse);

    // 4. Verificar la respuesta (esperar "250 Rename successful")
    if (!rntoResponse.StartsWith("250"))
    {
        Console.WriteLine("Error: El servidor no aceptó el comando RNTO.");
        return;
    }

    Console.WriteLine("Archivo renombrado exitosamente.");
}

void AbortCommand()
    {
        // 1. Enviar el comando ABOR
        SendCommand("ABOR");
        string abortResponse = ReceiveResponse();
        Console.WriteLine(abortResponse);

        // 3. Cerrar la conexión de datos (si está abierta)
        if (data_socket != null)
        {
            data_socket.Close();
        }
    }

void DeleteFile(string filePath, string fileName)
{
    string fullPath = $"{filePath.TrimStart('/')}/{fileName}";

    try
    {
        SetPassiveMode();

        // Eliminar archivo
        SendCommand($"DELE {fullPath}");
        Console.WriteLine(ReceiveResponse());

        data_socket.Close();
    }
    catch (Exception ex)
    {
        Console.WriteLine("Error: " + ex.Message);
    }
}

void MakeDirectory(string directoryName)
{
    SendCommand("MKD " + directoryName);
    string mkdResponse = ReceiveResponse();
    Console.WriteLine(mkdResponse);
}

void RemoveDirectory(string directoryName)
{
    SendCommand("RMD " + directoryName);
    string mkdResponse = ReceiveResponse();
    Console.WriteLine(mkdResponse);
}

void PrintWorkingDirectorySocket()
    {
        // 1. Enviar el comando PWD
        SendCommand("PWD");
        string pwdResponse = ReceiveResponse();
        Console.WriteLine(pwdResponse);


        // 3. Analizar la respuesta para extraer el directorio
        string currentDirectory = null;
        Regex regex = new Regex("\"(.*?)\"");
        Match match = regex.Match(pwdResponse);
        if (match.Success)
        {
            currentDirectory = match.Groups[1].Value;
        }

        Console.WriteLine("Directorio de trabajo actual: " + currentDirectory);
    }

string ListFiles(string path = "")
    {
        SetPassiveMode();

        SendCommand("LIST " + path);
        string response = ReceiveResponse();
        Console.WriteLine(response);

        //Recibir datos a traves del dataSocket
        string fileList = ReceiveData(data_socket);
        data_socket.Close();

        //Volver a establecer el modo pasivo para la proxima transferencia
        SetPassiveMode();

        return fileList;
    }

}

class Program
{
    public static void Main(string[] args){
        foreach (var item in args)
        {
            System.Console.WriteLine(item);
        }
        Console.ReadLine();
    }
}