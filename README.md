# Variation Normalizer Manuscript

## Set Up

To create the venv:

```shell
make devready
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
UTA_DB_URL=driver://user:password@host:port/database/schema
AWS_ACCESS_KEY_ID=dummy
AWS_SECRET_ACCESS_KEY=dummy
AWS_SESSION_TOKEN=dummy
PARSED_TO_CN_VAR_ENDPOINT=http://normalize.cancervariants.org/variation/parsed_to_cn_var
```

### Running the Variation Normalizer

Some notebooks involve running the variation-normalizer. See the [README](https://github.com/cancervariants/variation-normalization#backend-services) for setting up the backend services required.
