# Set up the Buyer app locally (Latest)

## Step1:
- Cloning the project (generate SSH Key on your system and add it to your profile on the code station)

  `git clone https://gitlab.com/transport-stack/ondc-micro-mobility-buyer.git`
- Ask the project maintainer for the latest working branch and checkout to that branch.
- Once cloning is done make the `.env` files running the below commands 
    ```bash
    cp ./envs/.env.common.sample ./envs/.env.common
    ```
  ```bash
    cp ./envs/.env.ondc.sample ./envs/.env.ondc
    ```
  ```bash
    cp ./envs/.env.keys.sample ./envs/.env.keys
    ```
  ```bash
    cp ./envs/.env.paytm.sample ./envs/.env.paytm
    ```
- Create an empty file `./envs/firebase_credentials.json`
- Ask the project maintainer for latest `.env.common`, `.env.ondc`, `.env.paytm` and `.env.keys` files
- Create `venv` and activate it
  ```bash
  python -m venv venv
  source venv/bin/activate
  ```
- Install packages and dependencies
  ```bash
  pip install -r requirements.txt
  ```
- Then run the command 
  ```bash
  export DJANGO_SETTINGS_MODULE=settings.base
  ```
## Step2:
- Run migrations 

  `python manage.py migrate`

## Step3:
- Initially load the project data by running the below command
  ```
  python -m setup.init
  ```
  
- This command also needs to be run whenever you are creating a new celery schedule task
  
## Step4:
- Start the app by running the below command

  ```python manage.py runserver <any port number>```


## Step5:
- Redis-server, Celery worker and Celery beat setup
- [Redis_setup](https://redis.io/docs/latest/operate/oss_and_stack/install/install-redis/)
- Start redis server on a separate server using the command (Make sure the redis server should run only once, on a single machine)
    ```
    redis-server
    ```

- Start celery worker by running these commands in a new terminal
    ```
    export DJANGO_SETTINGS_MODULE=settings.base
    ```
    ```
    celery -A ptx_core_backend worker --loglevel=info
    ```


- Start celery beat by running these commands in a new terminal
    ```
    export DJANGO_SETTINGS_MODULE=settings.base
    ```
    ```
    celery -A ptx_core_backend beat --loglevel=info
    ```

## Step6:
- Now you can start working by creating a new branch for yourself
- Branch naming convention would be like `dev_<yourname>`
- `git checkout -b dev_<yourname>`

## Step7: (Optional)
- setup ngrok follow this documentation
- [Ngrok_Setup](https://ngrok.com/docs/getting-started/?os=macos)
