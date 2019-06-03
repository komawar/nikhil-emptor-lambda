# nikhil-emptor-lambda

============
patronemptor
============

A sample project that uses Serverless Framework and Python 3.7 to create AWS Lambda function

First Version
-------------
- The project folder has been generated using the command 
  ``serverless create --template aws-python3 --path patronemptor``
  while created a template for the lambda function for python3.

- The serverless.yml file has been modified for to fit our function
  requirements. It also defines the lambda function, handler and method
  to be used. The function has been named as *weblambda* and this name
  should be used while invoking the function.

- If one wishes to deploy this service, the standard setup of
  serverless along with AWS credentials is required. Then
  ```serverless deploy -v``` is used to package and deploy this service
  to AWS lambda.

- To check what functions exist and if the above function has been
  deployed correctly, command```serverless deploy list functions``` can
  be used.

- The function takes *string* input and not *json*

- To invoke this lambda function command be used
  
        ``serverless invoke -f weblambda -l -d "http://example.com" --raw``

In this implementation there are a few assumptions:

- tracing has been enabled so any errors can be observed in AWS
  X-Ray Tracing service. Command line also gives a good error message,
  say in the case when no data is supplied. So, exception handling has
  been purposefully ignored.

- One (user) needs to supply the URL using the "-d" argument. "--raw"
  has been included in the example to indicate the app that it is a raw
  string, however, function simply works without it.

- Non alphabetical chars should be handled by this function.


Second Version
--------------
- The initial functionality of getting url as argument, making a request
  and extracting the title from it.

- A ``store_to_s3`` method within the lambda function, facilitates
  creation of bucket named "patronemptor-version2" using the boto's
  create_bucket call. This call being idempotent, even if bucket exists
  it should succeed with noop.

- The bucket name has been kept constant for the purposes of this code.

- An obj with ramdomly generated uuid stores the response body in this
  bucket.

- Object URL is generated using the AWS standard specifications and is
  returned to the call as a part of the json return response.

- It also adds a ```store_to_dynamodb``` method within the lambda
  function. This acts as facilitator for creation of a DynamoDB table
  named "version2" with a single attribute and key named "title". If
  table already exists it catches the "ResourceInUseException" and
  prints it, so that it can be logged to CloudWatch logs.

- A table entry is created to store the "title".

- To invoke this lambda function command
  
        ``serverless invoke -f weblambda -l -d "http://example.com" --raw``

In this implementation there are a few assumptions:

- The assumptions from first version of the project are valid.

- The bucket and table names are hardcoded in the code and their
creation is done by the lambda function itself.

- A serverless template to create these resources was made however due
to permission issues, that approach was not followed.

- The following error persisted while trying to create a S3 bucket and/or DynamoDB
  table using the serverless.yml (cloudformation stack). On debugging this for a
  while, playing with permissions and different yml configurations (including
  help from the web) no resolution was found. A many different approaches on
  stackoverflow were taken however, due to time constraint and weekend
  approaching serverless community on gitter was not done. As a result for time being
  a different approach to these resources was taken.
  
- Example error observed in the stack creation logs was:  
  
        `CloudFormation - CREATE_FAILED - AWS::DynamoDB::Table - myDynamoTable`

- To invoke this lambda function command be used
  
        ``serverless invoke -f weblambda -l -d "http://example.com" --raw``

Third Version
--------------

* A lambda function named `asyncinvoke` that receives a URL argument,
creates an ID for the same, stores in a DynamoDB record has been
introduced

* The DynamoDB table is attempted to be created by the function; if
already exists, the function catches corresponding exception, logs
and does not raise the exception

* The DynamoDB table `version3` Key is the above ID (type: uuid) as a
HASH key and no other Key is setup. A UUID should be enough to avoid
conflicts

* The record entry created in this process has the following
Attributes:
    - req_id (Key) (UUID) (String)
    - url (Attribute) (public access or permitted http(s) URL) (String)
    - recordstate (Attribute) (PENDING (pre-defined)) (String)

* The lambda function named `weblambda` has been refactored and is
invoked by the `asyncinvoke` lambda function

* It receives the UUID created above as an argument and reads the
record from table `version3`; makes a request to the URL stored
corresponding to the UUID and does the same processing as in previous
versions of the task

* The title and stored S3 object (of the response body) (processed
above) and recordstate (as PROCESSED) are updated to the Item
corresponding to the UUID

* lambda function `asyncinvoke`, asynchronously invokes the lambda
function `weblambda`

* Another lambda function `querydb` has been introduced to query the
DynamoDB table `version3` to get the record corresponding to the
supplied UUID and return the record data

* In this case, the record will be of two types as the one in PENDING
record state has only "req_id", "url", and "recordstate" attributes
while the other also has "title" and "s3_url"

* Corresponding changes to the serverless.yml file

* A side addition to .gitignore to remove tracking of IDE files

* To invoke *asyncinvoke* lambda function command be used
  
        ``serverless invoke -f asyncinvoke -l -d "https://supersimple.com/song/hello/" --raw``
  
* To invoke *querydb* lambda function command be used
  
        ``sls invoke -f querydb -l -d <uuid of the DB record>``
  

Fourth Version
--------------

* This version is an extension and modification of Third Version where
 `asyncinvoke` function does NOT asynchronously invoke `weblambda`.

* `weblambda` lambda function has been refactored to take input of the
DynamoDB stream instead of asynchronous or synchronous invokations.

* The DynamoDB table creation enables the stream during creation

* While the serverless.yml file should be able to solve the deployment
issues, a narrow, unresolved and conflicting error while creating the
DynamoDB table from the yaml file using CloudFormation stack has
resulted in commenting out the logic of creation of the table and
getting the Stream ARN that can be used to set in the *events stream*
section of the yaml file. This would be ideal logic for automating the
process however, in the interest of time and mischievous nature of the
issue, the assumption made is that the DynamoDB stream for this
function should be enabled from the console using the designer
configuration trigger option.

* The invocation is same as in Third Version.