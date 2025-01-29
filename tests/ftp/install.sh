ip=$(hostname -I)
docker run -d --rm --name vsftpd -p 20-22:20-22 -p 21100-21110:21100-21110 -p 990:990 -e "PASV_ADDRESS=${ip}" -v $PWD/tests/ftp/files:/home/vsftpd/user lhauspie/vsftpd-alpine 
echo "a new file for upload" >> tests/ftp/new.txt