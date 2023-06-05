# benchling-packager

This repository contains CloudFormation template which represents example of Benchling-Quilt integration.
It pushes Quilt packages on `v2.entry.created` and `v2.entry.updated.fields`
Benchling [events](https://docs.benchling.com/docs/events-reference) and updates back Benchling entries
with links to Quilt. It relies on using [schema](https://help.benchling.com/hc/en-us/articles/9684227216781) for Benchling entries.

## Installation

> FIXME: currently it works only in us-east-1 region, because lambda's layer is deployed only in that region

### 0. Generate template

```shell
python3 -m venv venv
. ./venv/bin/activate
python3 -m pip install -r requirements.txt
python3 make.py > build/template.yml
```

### 1. Subscribe to Benchling events

Setup subscription to Benchling events as documented [here](https://docs.benchling.com/docs/events-getting-started#setting-up-a-subscription).
These event types are required:

* `v2.entry.created`
* `v2.entry.updated.fields`

### 2. Setup Benchling app

Create Benchling app and grant it access as documented [here](https://docs.benchling.com/docs/getting-started-benchling-apps#creating-an-app).

### 3. Create CloudFormation stack

Create CloudFormation stack using template generated at step 0.
Pass name of event bus created at step 1 as `BenchlingEventBusName` parameter.
Pass client ID from settings of app created at step 2 as `BenchlingClientId`.

### 4. Set app secret

Under `Resources` tab of CloudFormation stack find `BenchlingClientSecret` and
click on its Physical ID.
Click `Retrieve secret value` and then `Set secret value`. Enter client Secret
from settings of app generated at step 2.

### 5. Create/update Entry schema

Create/update entry schema as explained [here](https://help.benchling.com/hc/en-us/articles/9684259067917).
It must have these fields:

| Name                  | Required  | Multi-select  | Definition    |
| --------------------- | --------- | ------------- | ------------- |
| Quilt+ URI            |           |               | Text          |
| Quilt DropZone URL    |           |               | Text          |
| Quilt Catalog URL     |           |               | Text          |
| Sentinel              |           |               | Integer       |

### 6. Test

Create new Benchling entry with schema created at the step 5, or set this
schema for existing entry.

Within minutes the package will be created and the entry fields will be
updated with links to this package.

> To refresh Quilt package from entry again you have to update `Sentinel`
field with arbitrary value.
