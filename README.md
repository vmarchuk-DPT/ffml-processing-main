# FFML Processing API

Processes the preprocessed data and adds it to analysis table

## Deployment Instruction :

> SSH into EC2 machine

```
ssh -i /path/to/private/key ec2-user@ec2-ipaddress
```

> Update files on EC2 machine

> Stop and delete the docker container and docker image
> Update the image and re-run the docker

```
cd processing-api/
sudo docker container ls // it will display the container id
sudo docker stop container-id
sudo docker rm container-id
sudo docker build -t fastapi-processing:latest .
sudo docker run -dp 80:80 fastapi-processing
```
