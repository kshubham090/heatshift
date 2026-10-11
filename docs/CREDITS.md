# Credits and licenses

Original HeatShift code is released under the [MIT License](../LICENSE). Dependencies, model weights and forecast data retain their own licenses; they are not relicensed by HeatShift.

| Component | Role | License / source |
|---|---|---|
| React and React DOM 19.3.0 | Interface | [MIT](https://github.com/facebook/react/blob/main/LICENSE) |
| Vite 6.4.4 | Frontend build tooling | [MIT](https://github.com/vitejs/vite/blob/main/LICENSE) |
| TypeScript 5.7.3 | Frontend types | [Apache 2.0](https://github.com/microsoft/TypeScript/blob/main/LICENSE.txt) |
| Lucide React 0.468.0 | Interface icons | [ISC](https://github.com/lucide-icons/lucide/blob/main/LICENSE) |
| FastAPI 0.143.0 | HTTP API | [MIT](https://github.com/fastapi/fastapi/blob/master/LICENSE) |
| Pydantic 2.14.0 | Input and output validation | [MIT](https://github.com/pydantic/pydantic/blob/main/LICENSE) |
| Strands Agents 1.59.0 | Agent tool orchestration | [Apache 2.0](https://github.com/strands-agents/harness-sdk/blob/main/LICENSE) |
| Ollama Python 0.6.3 / Ollama | Local model client / runtime | [Client MIT](https://github.com/ollama/ollama-python/blob/main/LICENSE), [runtime MIT](https://github.com/ollama/ollama/blob/main/LICENSE) |
| Qwen3, downloaded as `qwen3:1.7b` | Local tool-calling model | Apache 2.0; verified in the downloaded model's license. [Model source](https://huggingface.co/Qwen/Qwen3-1.7B) |
| HTTPX 0.28.1 / Uvicorn 0.54.0 | HTTP client / server | [HTTPX BSD 3-Clause](https://github.com/encode/httpx/blob/master/LICENSE.md), [Uvicorn BSD 3-Clause](https://github.com/Kludex/uvicorn/blob/main/LICENSE.md) |
| Mangum 0.22.0 / Boto3 1.43.111 | ASGI adapter / AWS SDK dependency | [Mangum MIT](https://github.com/Kludex/mangum/blob/main/LICENSE), [Boto3 Apache 2.0](https://github.com/boto/boto3/blob/develop/LICENSE) |
| Open-Meteo and contributing weather services | Forecast data | [CC BY 4.0 and API terms](https://open-meteo.com/en/terms), [data-source documentation](https://open-meteo.com/en/docs) |

Python licenses were inspected in installed distribution metadata and license files. Frontend versions and licenses were checked in the installed packages or lockfile. Keep the appropriate third-party license notices when redistributing dependencies.

## Strands source verification

The installed `strands-agents==1.59.0` distribution declares `Apache-2.0` and its packaged LICENSE contains Apache License, Version 2.0. Its actual `Project-URL` metadata points to [strands-agents/harness-sdk](https://github.com/strands-agents/harness-sdk), not an inferred repository name. The license link in the table follows that declared source. Documentation is at [strandsagents.com](https://strandsagents.com).

## Local model

The downloaded `qwen3:1.7b` model's Ollama inspection response returned an Apache 2.0 license and Q4_K_M quantization. The model tag is the reproducible configuration; model weights are downloaded separately and are not bundled in the repository. Earlier evidence may refer to a real `qwen3:4b` test; those are historical results, not the current default.

## Forecast data

Open-Meteo and its contributing national weather services provide the real forecasts. HeatShift includes attribution, the API source URL, forecast date, retrieval timestamp and requested/grid coordinates with every result. The free API is intended for noncommercial use under [Open-Meteo's terms](https://open-meteo.com/en/terms); its data are CC BY 4.0. A future commercial use needs an appropriate service arrangement.

## AI assistance disclosure

OpenAI Codex assisted with research, architecture, implementation, tests and documentation. The optional application assistant runs the configured local model through Strands. Scheduling, numerical comparisons and feasibility checks are performed by deterministic application code.
