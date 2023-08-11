# benchling-packager

The Benchling Packager automatically creates a dedicated Quilt package for every Benchling notebook,
to help ensure all your experiment data is:

- Findable
- Linkable
- Accessible
- Interoperable
- Reusable

within your AWS private cloud.

## How it works

Benchling Packager is an example
[CloudFormation template](https://aws.amazon.com/cloudformation/resources/templates/)
for Benchling-Quilt integration.
The template creates an [AWS Lambda function](https://aws.amazon.com/lambda/)
that is triggered by Benchling EventBridge events.

The lambda will create or update a Quilt packages on the following
[Benchling EventBridge events](https://docs.benchling.com/docs/events-getting-started#event-types):

- `v2.entry.created`
- `v2.entry.updated.fields`

If the notebook has an appropriate [schema](https://help.benchling.com/hc/en-us/articles/9684227216781),
the lambda will also back-update the Benchling notebook entry with the following fields:

- `Quilt+ URI`
- `Quilt Revise URL`
- `Quilt Catalog URL`

## Installation

You will need access to both the AWS Console and Benchling Admin Console to complete the configuration.
You will also need:

- Your Benchling tenant domain
- Your AWS Account ID (e.g. 12345689123)
- The AWS Region (e.g., us-west-2) you want to process events in
- An Event Bus Name (e.g., quilt-integration)

### 1. Create an event subscription in your Benchling tenant

From your Benchling tenant, use that event bus name and your AWS account ID to subscribe to
[Benchling events](https://docs.benchling.com/docs/events-getting-started#setting-up-a-subscription)

1. Go to `https://<YOUR_TENANT>.benchling.com/event-subscriptions`,
or go navigate to the settings menu > Feature settings > Developer Console,
which takes you to the Events page

2. Click the “+” button, which should open the following modal:
![Create subscription modal](https://files.readme.io/41badd0-image_3.png)

3. Fill in the:
    1. AWS Account ID
    2. AWS Region
    3. Event Bus Name
    4. Event Types: `v2.entry.created` and `v2.entry.updated.fields`

4. Click “Create"

This will also create a Partner Event Source in your AWS account.

### 2. Create a custom event bus in AWS

As soon as you create a new event subscription in Benchling,
you should **immediately** create a corresponding event bus in AWS.
Otherwise, the source may be automatically deleted,
which would require a support ticket to restore.

1. Go to the [Partner Event Sources](https://console.aws.amazon.com/events/home#/partners)
   for your region.
2. Click the name of the Partner Event Source created in the previous step,
   e.g. `aws.partner/benchling.com/<YOUR_TENANT>/quilt-integration`
3. Click `Associate with event bus`
4. Click `Associate`.

This will create a new event bus in your AWS account
with the exact same name as the Partner Event Source.
You will need this name when you create the CloudFormation stack.

Don't worry about creating an "Events Rule" in AWS.
That will be handled via CloudFormation.

### 3. Setup Benchling app

It is best to run each stack using its own credentials.

#### 3.1 Create a new Benchling app

You get these credentials by
[creating a Benchling app](https://docs.benchling.com/docs/getting-started-benchling-apps#creating-an-app)
and giving it access to your tenant:

1. In the Benchling Developer Console, click "Apps"
   (in the left sidebar, right above "Events)
2. Click `Create app` -> `From scratch`
3. Enter the App Name (and optional Description)
4. Select "Manual" for Lifecycle Management
5. Click `Create`

#### 3.2 Create a new Benchling app secret

This takes you to the app settings page.

1. Click `Generate secret` to create the `Client Secret` value.
2. Use the "copy" icon on the right to copy the `Client ID` and `Client Secret` values for use later.

NOTE: You do NOT need to explicitly add the app to your tenant,
since it was already created there.

### 4. Create CloudFormation stack

1. Download CloudFormation template [here](benchling_packager.yml)
1. Go to the [CloudFormation](https://console.aws.amazon.com/cloudformation/home) service.
1. Select the region used in step 1.
1. Click `Create stack` -> `With new resources (standard)`
1. Under `Specify template` select `Upload a template file`
1. Click `Choose file` and select `benchling_packager.yml` which you downloaded earlier.
1. Click `Next` and enter a stack name, e.g. `benchling-packager`
1. Under `Parameters`:
    1. Enter the name of the event bus created at step 1 as `BenchlingEventBusName`.
    1. Enter the client ID from settings of app created at step 2 as `BenchlingClientId`.
    1. Enter the your Benchling tenant name (i.e. $BenchlingTenant in https://$BenchlingTenant.benchling.com) as `BenchlingTenant`.
    1. Enter the name of the S3 bucket to use for storing packages as `DestinationBucket`.
    1. Optional: change the `PackageNamePrefix` used when creating new packages (default: `benchling/`).
    1. Specify the hostname of your Quilt Catalog as `QuiltWebHost`
1. Click `Next`, then click `Next` again
1. Check `I acknowledge that AWS CloudFormation might create IAM resources.`
1. Click `Submit`

#### 4.1 Set app secret in CloudFormation stack

1. Under `Resources` tab of CloudFormation stack find `BenchlingClientSecret` and
click on its Physical ID.
2. Click `Retrieve secret value` and then `Set secret value`.
3. Enter client Secret from settings of app generated at step 2.

### 5. Create/update Entry schema

In order for the lambda to update Benchling with the package information,
the notebook must have a schema containing exactly the following fields:

| Name                  | Required  | Multi-select  | Definition    |
| --------------------- | --------- | ------------- | ------------- |
| Quilt+ URI            |           |               | Text          |
| Quilt Revise URL      |           |               | Text          |
| Quilt Catalog URL     |           |               | Text          |
| Sentinel              |           |               | Integer       |

You can either create a brand-new schema, or add these fields to an existing schema.
Each new notebook will need to have this schema applied to it.
You can either do this manually, or by adding the schema to a template.

See [Benchling docs](https://help.benchling.com/hc/en-us/articles/9684227216781) for more information.

### 6. Test

Create new Benchling entry with schema created at the step 5, or set this
schema for existing entry.

Within minutes the package will be created and the entry fields will be
updated with links to this package.

> To refresh Quilt package from entry again you have to update `Sentinel`
field with arbitrary value.
