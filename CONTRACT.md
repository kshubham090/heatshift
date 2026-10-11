# HeatShift API contract
Frontend React/TypeScript (Vite); backend Python/FastAPI; camelCase JSON. Times HH:MM, local Asia/Kolkata, 15-minute increments. One crew, one day, max 8 nonpreemptive tasks; shift max 12h. All responses are JSON.

PlanRequest:
```
{date:"YYYY-MM-DD", location:{name:"Delhi · DTU",latitude:28.75,longitude:77.12}, shiftStart:"08:00",shiftEnd:"17:00", breaks:[{start:"12:30",end:"13:00"}], thresholdC:32, tasks:[{id:"grounds",title:"Grounds cleanup",durationMinutes:60,earliestStart:"08:00",latestEnd:"17:00",baselineStart:"13:30",locked:false}]}
```

GET /api/health => {status:"ok",agent:{available:boolean,provider:string,model:string},version:string}
GET /api/weather?latitude=28.75&longitude=77.12&date=YYYY-MM-DD => Weather
Weather: {source:"Open-Meteo",fetchedAt:ISO,mode:"live"|"saved",date,timezone:"Asia/Kolkata",latitude,longitude,gridLatitude,gridLongitude,hours:[{time:"HH:MM",temperatureC:number,apparentTemperatureC:number,precipitationProbability:number|null}],attribution:string,sourceUrl:string,warnings:string[]}
No fabricated weather. Missing data = honest 503, with labeled date-matching cache only if available.

POST /api/optimize body PlanRequest => PlanResult:
```
{status:"improved"|"unchanged"|"planned"|"infeasible",schedule:[{taskId,title,start,end,locked,meanApparentTemperatureC}],baselineSchedule:[same],baselineValid:boolean,metrics:{workMinutes,baselineMeanApparentTemperatureC:number|null,proposedMeanApparentTemperatureC:number|null,deltaC:number|null,baselineHotMinutes:number|null,proposedHotMinutes:number|null,thresholdC},explanation:string,violations:string[],constraintChecks:[{label:string,passed:boolean}],weather:Weather,request:PlanRequest}
```
If baseline is invalid, don't report improvement against it; status planned if a feasible plan exists. Infeasible must explain actual conflicting constraints. Threshold is user-defined planning indicator, never medical. Optimize exact deterministic duration-weighted apparent temperature, preserve all work/windows/locks/breaks. Minimize changes as tie-break only. HTTP 422 for invalid input, 503 weather unavailable.

POST /api/agent body {message:string,plan:PlanRequest} => {message:string,proposedPlan:PlanRequest|null,result:PlanResult|null,trace:[{tool:string,status:"complete"|"error",summary:string}],provider:string,model:string,requiresApproval:boolean}. Genuine Strands tool execution; model unavailable returns 503 with clear error, never fake agent. Agent must propose changes for review; doesn't persist/approve them. Always call deterministic tools for scheduling/calculations. Tool to propose_plan must validate using same PlanRequest; caller applies proposedPlan only after approval.

GET /api/demo => {plan:PlanRequest}. Dynamic tomorrow IST date, valid editable illustrative campus scenario, not actual DTU operations.

Frontend calls relative /api; Vite proxies to localhost:8000. In production FastAPI serves dist. UI stores local history/accepted plan in localStorage (clearly local). POST approve may be local only; no external side effect. Export report printable and JSON includes raw request/result/weather provenance. Error objects should use detail string or normal Pydantic array (UI normalizes).
