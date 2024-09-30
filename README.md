# AWS S3 File Upload Trigger - API Invoker

This project sets up an AWS Lambda function that is triggered by S3 events to invoke Airflow REST APIs based on configurable patterns.

## Features

- S3 event-driven Lambda function
- Configurable trigger patterns and API endpoints
- VPC-bound Lambda for secure networking
- CloudFormation template for easy deployment
- IAM role with boundary policy for enhanced security

## Prerequisites

- AWS CLI installed and configured
- Python 3.8 or later
- An existing VPC and S3 bucket
- Permissions to create IAM roles and Lambda functions

## Architecture

```mermaid
graph TD;
    S3[S3 Bucket] -->|1 File Upload| EN[S3 Event Notification]
    EN -->|2 Trigger| LF[Lambda Function]
    LF -->|3 Read Config| CB[Config Bucket]
    LF -->|4 Get Auth Token| SM[Secrets Manager]
    LF -->|5 Invoke API| AF[Airflow REST API]
    LF -->|6 Log Events| CW[CloudWatch Logs]
    LF -->|7 Emit Metrics| CM[CloudWatch Metrics]
    CM -->|8 Trigger Alarm| AL[CloudWatch Alarm]
    AL -->|9 Send Notification| SNS[SNS Topic]
    SNS -->|10 Alert| U[User/Admin]

    subgraph VPC
    LF
    end

    classDef aws fill:#FF9900,stroke:#232F3E,stroke-width:2px,color:#232F3E;
    classDef external fill:#1EC9E8,stroke:#232F3E,stroke-width:2px,color:#232F3E;
    class S3,EN,LF,CB,SM,CW,CM,AL,SNS aws;
    class AF,U external;
```

## Deployment

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/s3-airflow-trigger.git
   cd s3-airflow-trigger
   ```

2. Update the `config/sample_config.json` file with your specific trigger patterns and API endpoints.

3. Deploy the CloudFormation stack:
   ```
   aws cloudformation create-stack --stack-name AirflowTriggerStack \
     --template-body file://templates/cloudformation.yaml \
     --parameters \
       ParameterKey=VpcId,ParameterValue=vpc-12345678 \
       ParameterKey=SubnetIds,ParameterValue=subnet-12345678,subnet-87654321 \
       ParameterKey=S3BucketName,ParameterValue=my-existing-bucket \
       ParameterKey=ConfigBucketName,ParameterValue=my-config-bucket \
       ParameterKey=ConfigKey,ParameterValue=config.json \
       ParameterKey=PermissionsBoundaryPolicy,ParameterValue=arn:aws:iam::123456789012:policy/MyBoundaryPolicy \
     --capabilities CAPABILITY_IAM
   ```

   Replace the parameter values with your own VPC, subnet, and S3 bucket information.

4. Upload your configuration file to the specified S3 bucket:
   ```
   aws s3 cp config/sample_config.json s3://my-config-bucket/config.json
   ```

## Usage

Once deployed, the Lambda function will automatically be triggered when files are uploaded to the specified S3 bucket. It will check the uploaded file against the patterns in the configuration file and invoke the corresponding Airflow API if a match is found.

To update trigger patterns or API endpoints, simply modify the configuration file in the S3 bucket. The Lambda function will use the updated configuration on its next invocation.

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.
