# my-cloud django webapp

My cloud is a webapp developed with [django framework](https://www.djangoproject.com/)
using [PostgreSQL](https://www.postgresql.org/) and running on [nginx](https://nginx.org/)
web server. My cloud allows you to handle files in a filesystem and encrypt/decrypt them using 
[Shamir's Secret Sharing](https://cs.jhu.edu/~sdoshi/crypto/papers/shamirturing.pdf).

**Warning**

This app has been developed for demonstration purposes, is not meant to be used in production


## installation

### prerequisites

1. Docker version 18.09.3
2. docker-compose version 1.18.0

### installation steps

Clone the repository

```
$ git clone https://github.com/t04st3r/my-cloud.git
```

Enter inside docker folder

```
$ cd my-cloud/docker
```

Build docker images using docker-compose

```
$ docker-compose build
```

Create and start containers

```
$ docker-compose up -d
```

Test the webapp is up and running by connect on `http://localhost:8000`
with your favourite browser