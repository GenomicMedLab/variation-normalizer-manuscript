# Variation Normalizer Manuscript

## Set Up

### Creating the virtual environment

#### For Developers

The [requirements-dev.txt](./requirements-dev.txt) specifies general package requirements.

To create the venv:

```shell
make devready
source .venv/bin/activate
pre-commit install
```

#### For reproducing analysis

The [requirements.txt](./requirements.txt) is a lockfile containing exact versions used.

To create the venv:

```shell
make reproduce
source .venv/bin/activate
pre-commit install
```

### Environment Variables

We use [python-dotenv](https://pypi.org/project/python-dotenv/) to load environment variables from the `.env` file in the root directory:

```markdown
.
├── .env
└── README.md
```

Some environment variables that need to be set are (replace with actual values):

```env
GENE_NORM_DB_URL=http://localhost:8000
UTA_DB_URL=driver://user:password@host:port/database/schema
AWS_ACCESS_KEY_ID=dummy
AWS_SECRET_ACCESS_KEY=dummy
AWS_SESSION_TOKEN=dummy
```

If you do not have an AWS account, you can keep `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_SESSION_TOKEN` as is. Local DynamoDB instances will allow dummy credentials.

### Running the Variation Normalizer

Some notebooks involve running the variation-normalizer. See the [README](https://github.com/cancervariants/variation-normalization#backend-services) for setting up the backend services required.
