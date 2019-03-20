deploy-button :ship: :red_circle:
======

CodePipeline supports Manual Approval actions that allow you to put manual gates in your pipeline. IoT Buttons allow you to have a real world button hooked up to a Lambda function. This project configures your IoT button to approve (or reject) your CodePipeline manual approval steps.

*This is currently a work in progress; nothing actually is working right now.*

What's in the box
------

The `deploy-button` project utilizes several AWS services to get things working. 

* CodePipeline:
  *  Sample Pipeline
* SNS Topics:
  * Notify for Manual Approvals
* Lambda Functions:
  * Process button press
  * Send Notification
* IoT:
  * Thing
  * Policy
  * Rule
  * Certificate

Workflow:
------
After you've run the CloudFormation templates to create everything, the pipeline will execute and the follow steps will occur:
* Code Pipeline hits "Manual Gate" stage.
* It triggers a a lambda function that does two things:
   * Stores the CodePipeline approval token in 
   * Sends SNS notification
* Then CodePipeline sits at the Manual Approval stage.

Once the pipeline stops at the approval action, your IoT button can accept or reject the changes by either long pressing (accept) or short pressing (deny) the button.
* Button press triggers a lambda function
* Lambda function receives the press information and decides it is approval or rejection
* It looks up the approval token in SSM
* It then calls the CodePIpeline API and sends the approval / rejection.


Commands:
-----
First you have to configure the IoT button to connect to your AWS account. This is done by create keys and certificates that you'll need to upload to the button. First we'll create the keys and certs:

    # first thing: generate IOT cert
    aws iot create-keys-and-certificate --set-as-active --output json > keys-and-cert.json
    export cert_arn=$(cat keys-and-cert.json | jq '.certificateArn' | tr -d '"')
    cat keys-and-cert.json | jq '.certificatePem' | tr -d '"' | awk '{gsub(/\\n/,"\n")}1' > certificate.pem
    cat keys-and-cert.json | jq '.keyPair.PrivateKey' | tr -d '"' | awk '{gsub(/\\n/,"\n")}1' > private.key
    rm keys-and-cert.json

You'll also want to run these two commands and note the output:

    aws iot describe-endpoint | jq .endpointAddress | tr -d '"' | awk -F. '{ print $1}'
    aws iot describe-endpoint | jq .endpointAddress | tr -d '"' | awk -F. '{ print $3}'

Next is the annoying bit: the IoT button is configured by connecting to it's wireless network and pulling up a webpage. You'll need to put the IoT button into configuration mode, connect to it from your computer, and then enter in the appropriate information.
1. Hold down the IoT button for 10 seconds, until the light begins flashing blue.
2. A wireless network will appear, named something like `Button-ConfigureMe`, connect to it.
3. Navigate to http://192.168.0.1/index.html
4. Enter your wifi information -- *note*: if you're on a network that configures wifi via a redirect, you won't be able to use your IoT button.
5. Under `AWS IoT Configuration`
  * For `Certificate` upload the file you created above `certificate.pem`
  * For `Private Key` uploaded the file you created above `private.key`
  * For `Endpoint Subdomain` enter the output from the first command above.
  * For `Region`, enter the output from the second command above.
 6. Check the agreement to terms and conditions box
 7. Click `Configure`
 8. Reconnect to your nomal wireless network.

The IoT button will blink red -- that's because we're doing things slightly out of order than it prefers, so don't worry about it. With IoT button is configured, we can set up the resources to support it. You'll need to set the values of the first two variables.


    # The DSN will be on the back of your IoT button
    export iot_button_dsn=1234567890
    export github_token=12345678908754321
    # this can be whatever you like, leaving it as is should work too.
    export lambda_bucket=test-lambda-functions-$(date +%Y%m%d%H%M%S)
    aws s3 mb s3://$lambda_bucket

    sns_stack_name="deploybutton-sns-$(date +%Y%m%d%H%M%S)"
    aws cloudformation create-stack \
      --stack-name $sns_stack_name \
      --template-body file://provisioning/sns.yml \
      --capabilities CAPABILITY_IAM

    export lambdas_stack_name=deploybutton-lambdas-$(date +%Y%m%d%H%M%S)
    aws cloudformation package --template-file provisioning/lambdas.yml --s3-bucket $lambda_bucket --output-template-file /tmp/packaged.yml
    aws cloudformation deploy --template-file /tmp/packaged.yml --stack-name $lambdas_stack_name --capabilities CAPABILITY_IAM

    aws cloudformation create-stack \
      --stack-name "deploybutton-iot-button-$(date +%Y%m%d%H%M%S)" \
      --template-body file://provisioning/iotbutton.yml \
      --capabilities CAPABILITY_IAM \
      --region us-east-1 \
      --parameters \
        ParameterKey="IoTButtonDSN",ParameterValue="$iot_button_dsn" \
        ParameterKey="CertificateARN",ParameterValue="$cert_arn" \
        ParameterKey="ButtonListenerLambdaArn",ParameterValue="$(aws cloudformation describe-stacks --stack-name $lambdas_stack_name --query Stacks[*].Outputs[?OutputKey==\'ButtonListenerLambdaArn\'].OutputValue --output text)"

    aws cloudformation create-stack \
      --stack-name "deploybutton-codepipeline-$(date +%Y%m%d%H%M%S)" \
      --template-body file://provisioning/codepipeline.yml \
      --capabilities CAPABILITY_IAM \
      --parameters \
        ParameterKey="GitHubToken",ParameterValue="${github_token}" \
        ParameterKey="NotificationFunction",ParameterValue="$(aws cloudformation describe-stacks --stack-name $lambdas_stack_name --query Stacks[*].Outputs[?OutputKey==\'SendNotificationLambdaName\'].OutputValue --output text)"


Bonus:
-----
This project leverages IoT, which you may need to troubleshoot. Unfortunately, IoT doesn't come with CloudWatch Logs enabled. You can use this template and command to enable IoT pushing logs to CloudWatch logs on your account.

    iot_logging_role_stack="iot-log-role-$(date +%Y%m%d%H%M%S)"
    aws cloudformation create-stack \
      --stack-name $iot_logging_role_stack \
      --template-body file://provisioning/iot-log-role.yml \
      --capabilities CAPABILITY_IAM
    # wait for stack to complete
    sleep 30
    aws iot set-v2-logging-options \
        --role-arn $(aws cloudformation describe-stacks --stack-name $iot_logging_role_stack --query Stacks[*].Outputs[?OutputKey==\'IoTLogRole\'].OutputValue --output text) \
        --default-log-level INFO

After you run that, IOT should log to the CloudWatch Log Group `AWSIotLogsV2`.
