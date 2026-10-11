# HeatShift data and privacy

HeatShift is a hackathon prototype for non-sensitive planning. It has no user accounts, authentication or private-team workspace. Use illustrative job descriptions or inputs you are comfortable processing on the selected app host and model provider.

The submitted configuration runs on the local machine with Ollama. It makes no AWS cloud inference requests and creates no paid cloud resources. Cloud deployment files are not included in this submission. An inactive Bedrock provider remains in the application code; it is not used by the local workflow.

## Data flow

| Information | Where it goes |
|---|---|
| Location name, coordinates, selected date, jobs, windows, locks, shift, breaks and threshold | From the browser to the HeatShift backend when a plan is calculated or an assistant request is sent. |
| Requested coordinates and forecast date | From the backend to Open-Meteo to fetch weather. Worker names and task titles are not needed by that service. |
| Assistant message, plan details and tool results | To the local Ollama server through Strands in the submitted configuration. The unused optional Bedrock adapter would instead use the configured AWS service. |
| Accepted plan and result | In this browser's local storage under `heatshift-accepted`. The stored record includes the plan, weather evidence and acceptance timestamp. |
| Exported JSON or printed report | To the destination the user chooses. Reports contain the location, jobs, schedule and weather evidence. |

“Local Ollama” means the Ollama server configured for the backend. If the backend is hosted elsewhere, inference happens on that host, not automatically on the visitor's device. A non-local `OLLAMA_HOST` sends data to that configured endpoint. Bedrock processing is governed by the selected AWS account, region, service terms and configuration.

## Storage and logs

The application does not create a database of plans or persist assistant conversations. Request-local state exists in process memory while a request runs. The weather adapter keeps up to 128 real forecast responses in memory; cached results are keyed by requested coordinates and date, retain their retrieval timestamp and are explicitly labeled saved. They disappear when that process is replaced or restarted.

The backend also uses a bounded, in-memory IP-based request limiter for the planning endpoints. Local server access logs can contain connection metadata and request paths; weather GET request paths may include coordinates. The app avoids returning raw model/provider error bodies, prompts or credentials in errors. The current build has no AWS logging resources. Log retention on a later hosting platform would depend on that platform's configuration.

This code does not include an analytics or advertising integration. Review any changes to deployment, logging or frontend assets before treating that statement as applying to a modified installation.

## Local acceptance and deletion

Accepting a plan saves one accepted result in the current browser. It does not notify a crew, assign a job, track a person or create a server audit record. Anyone with access to that browser profile may be able to view the saved plan. Clear the site's browser storage to remove it; this also removes the accepted-plan record. Delete downloaded reports separately if they are no longer needed.

No GPS permission is required for the default scenario. The selected coordinates are editable planning inputs. Avoid adding personal health details, worker names, passwords, access keys or confidential work orders to the plan or assistant message.

## Prototype boundaries

The documented workflow binds the application to the local loopback interface. Its endpoints have no authentication. Request limits are controls within each running process, not a private-workspace security boundary. Authentication, organization isolation, explicit retention policies and audited access controls would be required before exposing the app for sensitive operational use.

HeatShift uses weather as a planning input. It does not collect health measurements or establish a person's safe exposure to heat.
