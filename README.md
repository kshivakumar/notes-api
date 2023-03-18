# Introduction
This repo contains a backend API for a note-taking application. The project is implemented in Python using the Django framework, showcasing various aspects of backend development including API design, database management, and server-side logic.

## High level implementation
A typical note-taking app has a collection of notebooks, each notebook contains pages and each page holds the actual content.
This structure is similar to Evernote, OneNote and Notion. Google Keep, however only has pages and no notebooks.

A note-taking app is a write-heavy application with fewer reads but extremely large number of writes and updates. To provide maximum reliability to the end-user, ideally every key-stroke should be saved.

In the simplest implementation, the client sends the whole page content as one long string to the server everytime the user makes any change--adding, modifying or deleting text. The server then replaces the existing data in the database with the latest received from client. This is how Google Keep seems to handle plain text notes.

The downside of this approach is visible when thousands of users simultaneously modify their pages containing large amount of content. This leads to increased data transfer, increased server load and higher database write load.  

Instead of treating the whole page as a single string we can break down the content into blocks of different types:
 - Header - Page title, H1, H2, H3
 - Paragraph - Text paragraph, Code block, Block quote
 - List - Ordered/unordered list, To-Do list
 - Image/Video (only links with preview)
 - Table
 - ...more

Since all the elements are in sequence, the page can be considered as an array of blocks. Each block is composed of metadata and the actual content. 

Whenever the text corresponding to a block is updated on the client side, only that block's metadata and content is sent to the server. The server replaces the existing block content with the latest content in the database.

This approach is semantically correct since users interpret a page's content as a sequence of various elements, not a single string. Manipulating the page at this semantic level by targeting individual elements offers two main advantages:
- On the backend, both the app server and database have better performance compared to the simple 'rewrite whole page' implementation due to dealing with less data.
- On the client side(web ui, mobile app), it facilitates easier management of page presentation for client applications allowing them to create more sophisticated and responsive UIs.

**The current implementation follows this approach.**

This is how Evernote and OneNote handle page updates. Even Google Keep uses this approach for handling to-do lists.  

> Notion follows a even more granular approach where it sends only the modified text from the block and _not the entire block_.  
This approach is trickier to implement and may not be significantly more efficient than the current method to justify its added complexity. Nevertheless, it will be explored in the future.

Note:  
I was able to decipher the behaviour of Evernote, OneNote, Keep and Notion by tracking the request/response entries in Network Tab in browser's Developer Tools. 

# Project Goals
The ultimate objective of this project is to develop the API to production-grade standards, ensuring it is robust, performant, secure, cost-efficient, and ready for real-world deployment.

# Current State
The majority of planned API endpoints and core features have been implemented.  

Security and performance haven't been focused on yet. The plan is to first add all the features usually found in popular note-taking apps. Next, app profiling and load testing will be done, followed by performance improvements. Security improvements will be done at the end.

## Technology Stack:
**Backend**: Python, Django, [Django Rest Framework (DRF)](https://www.django-rest-framework.org/), [Gunicorn](https://docs.gunicorn.org/en/stable/)  
**Database**: PostgreSQL  
**Deployment**: AWS, [Terraform](https://developer.hashicorp.com/terraform/intro)  

**Development Tools**: [black](https://black.readthedocs.io/en/stable/)(code formatting)

## API Endpoints
- **/user**  
`GET` dictionary of user details, preferences(themes, UI flags), last_viewed_page, etc.

- **/notebooks**  
`GET` user's notebooks (id and title)  
     Params: order, filters, pagination, prefetch notebook list  
`POST` create a new notebook

- **/notebooks/reposition**  
`POST` reposition a notebook (custom ordering)

- **/notebooks/<notebook_id>**  
`GET` notebook details  
`PUT/PATCH/DELETE` notebook

- **/notebooks/<notebook_id>/pages**  
`GET` notebook's page ids and titles  
     Params: order, filters, pagination, prefetch page list  
`POST` create a new page

- **/notebooks/<notebook_id>/pages/reposition**  
`POST` reposition a page within the same notebook (custom ordering)

- **/pages/move**  
`POST` move one or more pages to another notebook

- **/pages/<page_id>**  
`GET` page details  
`PUT/PATCH/DELETE` page details such as title and metadata

- **/pages/<page_id>/blocks**  
`GET` page's block ids  
     Params: pagination, prefetch blocks details  
`POST` add a new block

- **/pages/<page_id>/blocks/reposition**  
`POST` reposition a block within the same page

- **/blocks/<block_id>**  
`GET/PATCH/DELETE` a block

- **/recylebin**  
`GET` list of deleted notebooks and/or pages with pagination  
     Params: pagination

- **/recyclebin/<id>**  
`GET` retrieve a deleted page or notebook(with all its pages)  
`DELETE` permanently delete a notebook or page

- **/recyclebin/<id>/restore**  
`POST` restore a page/notebook

## Database Design
Reffer to the comments in the [models.py](api/models.py) for explanations of the database design decisions.

## Immediate Goals
### Application
- Implement "restore notebooks/pages" API
- Add "page tags" feature
- Implement "user registration" API
- Add more test cases to cover all the existing APIs

### Deployment
- Make Terraform wait for user_data script to finish or use Packer to build custom AMI

# Local Setup

## Using virtualenv
1. Install dependencies:
   - Python 3.8+
   - Postgres 14+
2. Clone the repository
   - `git clone git@github.com:kshivakumar/notes-api.git`
   - `cd notes-api`
3. Create and activate virtual environment  
   - `python3 -m venv .venv`  
   - `source .venv/bin/activate`
4. Install packages  
   - `pip install -r requirements.txt`
5. Create a new database in Postgres
   - `CREATE DATABASE <new_db_name>;`
6. Set up environment variables:
   - Create a [`.env`](https://stackoverflow.com/questions/62925571/how-do-i-use-env-in-django) file in the project root,  
   **or**  
   Add variables to your shell rc file (e.g., `.bashrc`, `.zshrc`)
   - Required variables:  
     `DJANGO_DEBUG` (set to True)  
     `DJANGO_SECRET_KEY`  
     `DJANGO_DB_HOST` (not required if Postgres is running locally)  
     `DJANGO_DB_PORT` (not required if Postgres is running on default port 5432)  
     `DJANGO_DB_NAME` (use the new database name created above)  
     `DJANGO_DB_USERNAME`  
     `DJANGO_DB_PASSWORD`

7. Collect static files  
`mkdir -p notes_api/staticfiles`  
`python manage.py collectstatic`

8. Create sample data  
`python manage.py create_sample_data`

9. Start server  
`gunicorn --workers 3 --bind 0.0.0.0:8000 --access-logfile - notes_api.wsgi:application`

Access the api endpoint at http://localhost:8000/api

## Using Docker
1. Ensure [docker-compose](https://docs.docker.com/compose/install/) is available and Docker is up and running.
2. Run `docker-compose up`  
3. In a separate terminal, run this to create sample data  
`docker exec notes_api_server python manage.py create_sample_data`  

Access the api endpoint at http://localhost:8000/api

Log into Postgtres database using   
`docker exec -it notes_api_database psql -U postgres -d notes_api`

# Deployment
Terraform is used to manage the infrastucture on AWS.

[Install Terraform and configure IAM role and credentials in AWS.](https://blog.gruntwork.io/an-introduction-to-terraform-f17df9c6d180#a9b0)

The default configuration(see ./deployment/dev.auto.tfvars) uses `ap-south-2` as VPC Region. Update the value as per your needs.  
Accordingly, update `image_id` since different regions use different image ids for same OS. Use image id of `Amazon Linux 2` only.  
To access EC2 instance through SSH, update `ec2_key_name` with a [new](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-key-pairs.html) or existing key-pair name.  

Deploy to AWS using
1. `terraform init`
2. `terraform apply -auto-approve`

Terraform will output the API endpoint and the command to connect to Postgres instance. These resources are accessible only from your public IP address.

> **Note**: The API server is not immediately accessible after Terraform completes the infrastructure provisioning. The `user_data` script(`./deployment/setup.sh`), which installs dependencies, runs Django commands and initializes Gunicorn, requires additional time to execute.
>
> **Please wait at least 60 seconds after provisioning before attempting to access the API endpoint.**

Sample data is already created as part of the deployment.  
See `./api/management/commands/create_sample_data.py` for sample user login details.

Run `terraform destroy -auto-approve` to clean up the infrastructure after you are done testing.
