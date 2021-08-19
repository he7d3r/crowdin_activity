# Generating Translation Reports from Crowdin Activity logs

## Usage

To generate a CSV with the translation activities for a project whose URL is
`<https://crowdin.com/project/<project_name>`, run the following command in the
terminal:

```bash
PROJ_NAME=<project-name> OUTPUT=crowdin.csv docker-compose up --build
```

After a few minutes, it will create a CSV file with the data for the activities
found on Crowdin (the time will be longer the more data there is to collect).
