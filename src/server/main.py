import server
import argparse

def parseArgs():
  parser = argparse.ArgumentParser(description="start the server")
  parser.add_argument("-s", "--secure", type=bool, default=False, help="indicates the use of https")
  
  args = parser.parse_args()
  return args.secure

def main():
  secure = parseArgs()
  if secure:
    cert="cert.pem" #para esto hay que generar un certificado y una llave con el comando openssl etetc.etc. y copiarlos en la raiz del repo
    key="key.pem"
    server.start_server(port=8443, cert=cert, key=key) #8443 para pruebas locales porque de 1024 para abajo estan reservados para root
  else:
    server.start_server()
  
if __name__=="__main__":
  main()