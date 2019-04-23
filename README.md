deploy-button :ship: :red_circle:
======

CodePipeline supports Manual Approval actions that allow you to put manual gates in your pipeline. IoT Buttons allow you to have a real world button hooked up to a Lambda function. This project configures your IoT button to approve your CodePipeline manual approval steps.

What's in the box
------

The `deploy-button` project utilizes several AWS services to get things working.

* CodePipeline:
  * Sample Pipeline
* Lambda Functions:
  * Process button press
* IoT:
  * Thing
  * Policy
  * Rule
  * Certificate

Workflow:

------
After you've run the CloudFormation templates to create everything, the pipeline will execute and the follow steps will occur:

* Code Pipeline hits "Manual Gate" stage and waits.
* Once the pipeline stops at the approval action, your IoT button can accept the changes by pressing the button.
* Button press triggers a lambda function
* Lambda function receives the press information and looks up the pipeline information.
* It then calls the CodePipeline API and sends the approval.

Commands:

------
First you have to configure the IoT button to connect to your AWS account. This is done by create keys and certificates that you'll need to upload to the button. First we'll create the keys and certs:

    # first thing: generate IOT cert
    aws iot create-keys-and-certificate --set-as-active --output json > keys-and-cert.json
    export cert_arn=$(cat keys-and-cert.json | jq -r '.certificateArn')
    cat keys-and-cert.json | jq -r '.certificatePem' | awk '{gsub(/\\n/,"\n")}1' > certificate.pem
    cat keys-and-cert.json | jq -r '.keyPair.PrivateKey' | awk '{gsub(/\\n/,"\n")}1' > private.key
    rm keys-and-cert.json

You'll also want to run these two commands and note the output:

    echo "Endpoint Subdomain: $(aws iot describe-endpoint | jq -r .endpointAddress | awk -F. '{ print $1}')"
    echo "Region: $(aws iot describe-endpoint | jq -r .endpointAddress | awk -F. '{ print $3}')"

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
    # The Github token you'll need to generate from your github account page
    export github_token=12345678908754321
    # this can be whatever you like, leaving it as is should work too.
    export lambda_bucket=test-lambda-functions-$(date +%Y%m%d%H%M%S)
    aws s3 mb s3://$lambda_bucket

    export lambdas_stack_name=deploybutton-lambdas-$(date +%Y%m%d%H%M%S)
    aws cloudformation package \
      --template-file provisioning/everything.yml \
      --s3-bucket $lambda_bucket \
      --output-template-file /tmp/packaged.yml
    aws cloudformation deploy \
      --template-file /tmp/packaged.yml \
      --stack-name $lambdas_stack_name \
      --capabilities CAPABILITY_IAM \
      --parameter-overrides \
        ParameterKey="IoTButtonDSN",ParameterValue="$iot_button_dsn" \
        ParameterKey="CertificateARN",ParameterValue="$cert_arn" \
        ParameterKey="GitHubToken",ParameterValue="${github_token}"

Bonus:

------
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

Feedback / Questions / Issues:

------
If you hit any issues getting any of this to run, or if you really have any feedback at all, please open up a Github issue. Also, please feel free to write your own improvements and open up a pull request!
