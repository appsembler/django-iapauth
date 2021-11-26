# Klanten
A microservice for customer ids.

> “klanten” just means “**customers**” in Dutch.

## Development
To start developing on this module, clone it and fix yourself a cup of coffee.

```console
$ git clone git@github.com:appsembler/klanten.git
$ cd klanten
```

## Authentication
Since this library is going to be used by other applications, we give a 
permission to view/edit resources using two mechanisms:
- Django model permissions for an authenticated user.
- API keys.


### Creation
If you are a superuser and you want to create a new API key for your 
application, got to the **API keys** table in the admin panel and click on
*ADD API KEY* button in the top right corner, fill out the form, and don't 
forget to store the API Key somewhere as you're not going to have access to it 
later.

> To create a new superuser account, please reach out to the orange team to help
you.


### Usage

By default, clients must pass their API key via the Authorization header. 
It must be formatted as follows:

```
Authorization: Api-Key ********
```

In python
```python
TOKEN = '********'
headers = {'Authorization': f'Api-Key {TOKEN}'}
```
where `********` refers to the generated API key.


### Grant scheme
Access is granted if and only if all the following is true:

- The configured API key header is present and correctly formatted.
- A usable API key with the prefix of the given key exists in the database.
- The hash of the given key matches that of the API key.


## Usage
For your app to interact with Klanten, you can use API calls in Python script. 
There are multiple end-points your app can reach to.

### Create a customer record
To create a record for the customer in Klanten, use `create` procedure. 

> **NOTE** 
> If the customer record already exists we will return the original value back.

```python
import requests

url = 'http://127.0.0.1:8000/v1/customers/'

# customer_domain will allow us to distinguish different customers.
customer_domain = 'ahmed.jazzar.com'
r = requests.post(url, data={'domain': customer_domain}, headers=headers)
```

Output
```python
r.content
b'{"domain":"ahmed.jazzar.com","uuid":"1e6e817d-c3d7-432f-ae47-ed75b4744fce"}'
```

You can also call this procedure to create as many mappings as you wish for 
your customers. However, we will prevent the same user from having multiple
mappings in the same app. 


### Create a customer mapping
Creating a mapping for a customer is the official way of telling Klanten that
a specific customer do use the calling app/service. It also allows you to
request this customer's UUID later when needed.

```python
url = 'http://127.0.0.1:8000/v1/mappings/'
data = {
    "customer_app_id": "username",
    "customer": "1e6e817d-c3d7-432f-ae47-ed75b4744fce",
    "app": "amc"
}
r = requests.post(url, data=data, headers=headers)
```

Output
```python
r.status_code
201

r.content
b'{"customer":"1e6e817d-c3d7-432f-ae47-ed75b4744fce","customer_app_id":"username","app":"amc"}'
```

### Get Customer's UUID
To get the UUID value of a customer, you can use `get` procedure. 

> **NOTE** 
> If no record found for the given UUID, a Customer.DoesNotExist error is
> going to be thrown.

```python
app = 'edx'
customer_app_id = 'jazzar'
url = f'http://localhost:8000/v1/query/{app}/{customer_app_id}'
r = requests.get(url, headers=headers)
```

Output
```python
r.status_code
200

r.content
b'{"domain":"ahmed.jazzar.com","uuid":"1e6e817d-c3d7-432f-ae47-ed75b4744fce"}'
```

### Get customer mappings
To get all the applications a UUID is associated with, use the following
```python
uuid = '6939ba9f-dfae-43fc-9e35-2054708a1e95'
url = 'http://127.0.0.1:8000/v1/mappings/'

data = {
    "customer": uuid,
}
r = requests.get(url, data=data, headers=headers)
```

Output
```python
r.status_code
200

r.content
b'[{"app":"amc","domain":"ahmed.jazzar.com","aoo_id":"1234"},{"app": "edx","domain":"ahmed.jazzar.com","aoo_id": "ajazzar"}]'
```

## Setup
### Local setup
#### Running the server
To run the server locally execute this command:
```console
$ make runserver
```

#### Management commands
We've added the most used django management commands to this project's 
[Makefile](https://github.com/appsembler/klanten/blob/master/Makefile).

Examples:
```console
$ make makemigrations
$ make createsuperuser
```

#### Running the tests
To run the test, simply run
```console
$ make
```

This will run both, flake8 and Django tests for you.

#### Virtual env
Klanten automatically handles the virtualenv for you so you don't have to worry
about it. However, what you need to know is:
- We read pip packages from `requirements.txt`.
- We use `python3`.
- All pip packages are installed in `ve/` dir.

If you want to clean your venv and the cached files run:
```console
$ make clean
```

#### Supported applications
To reduce errors and eliminate duplicated, we decided to pre-define the 
supported application from which you can store customer records. 
You can log into the admin panel to perform CRUD operations on supported 
applications. 


### GAE setup
#### Interacting with the database
App Engine doesn't have a straightforward way to interact with the database
through Django management commands like `manage.py migrate`. So, to allow your
commands to interact with the database, it has to be done locally but accessing
the production database. For that, we are using the GCP Cloud SQL Proxy. You 
run it locally, and it creates a secure tunnel to the Cloud SQL instance.

```console
$ make cloudsql.proxy  ## The tunnel will remain alive until you terminate the process
```

This tunnel must be alive every time you use a `gae.%` command. More details 
below.

If you dig into the previous make target you'll find it's using 
`cloud_sql_proxy` script. We fetch this script from Google using `curl` and 
`wget` depending on your OS. 
To simplify the process for you, just use the make target specifically designed 
for this purpose.

```console
$ make cloudsql
```

#### Deploying the application
To deploy the application to AppEngine you can run
```console
$ make deploy
```

> **NOTE**
> 
> This command assumes you've got the infrastructure ready. For more about the
> infrastructure visit [infrastructure/klanten](https://github.com/appsembler/infrastructure/tree/master/klanten)


For more details on how this works, please visit the great document by 
Anders here [Django PoC on GAE](https://appsembler.atlassian.net/wiki/spaces/ORANGE/blog/2020/08/25/782008517/Django+PoC+on+GAE)

#### Management commands:
To run the management commands make target on Google App Engine, just prefix 
the command with `gae.`.

Example:
```console
$ make gae.makemigrations
```

You just need to keep in mind that in order to interact with the cloud DB, you
need to create a secure tunnel to the Cloud SQL instance. See Interacting with 
the database section above.
