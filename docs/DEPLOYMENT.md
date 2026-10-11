# Zero-spend Build It route

HeatShift runs on your computer using the open-source AWS Strands Agents SDK and a local Ollama model. It does not create or call metered AWS cloud resources in the default configuration. AWS credits, payment details and AWS sign-in are not required for this route.

The event permits AWS open-source tools **or** AWS deployment and gives local and cloud projects the same judging consideration. The demo must show real Strands tool execution; an AWS logo alone is not sufficient.

## Run the full app locally
Follow [the README](../README.md). The backend listens at `http://127.0.0.1:8000`; the frontend at `http://127.0.0.1:5187`. Ollama listens locally on port 11434. The forecast is retrieved from Open-Meteo's noncommercial free API with attribution and caching.

For a single local web server after setup:
```sh
npm run build
HEATSHIFT_AGENT_PROVIDER=ollama HEATSHIFT_AGENT_MODEL=qwen3:1.7b python3 -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```
Then open `http://127.0.0.1:8000`. Start after the frontend build so the server mounts its assets.

## Share for judging
Publish the source repository and a YouTube demo under three minutes, as the rules require. A cloud-hosted live app URL is not required for the Build It route. Anyone with the required local runtime can reproduce the app and agent; the video should show the tool trace, forecast provenance, changed constraint, failure case and accepted plan.

## Cloud status
The default configuration remains local Ollama. Optional AWS packaging and CloudFormation files are included for a separately reviewed hosted deployment; see [AWS hosting review](AWS_HOSTING_REVIEW.md). Those files do not establish that a cloud stack has been deployed, and running the local instructions does not create one.
