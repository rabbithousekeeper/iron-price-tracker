# Development startup

At each session start call the connected Hjarni MCP `me`, then
`instructions_get({level: "brain"})`. Follow its existing project links to the
designated current sources, including repository procedures when
they are explicitly designated. Do not copy private Brain prose or identifiers
here. No project Brain link is currently recorded in this public checkout;
resolve it through the connected source before claiming project-canonical
alignment. Follow [CLAUDE.md](CLAUDE.md) for repository conventions.

This checkout adds only an optional local adapter, not another policy authority
or a permanent management ledger. Use existing evidence or temporary external
records. Keep private source identities, versions and read evidence outside this
public repository. Distinguish observations from current requirements; an old
unfinished log does not create new work. If a necessary source cannot be read,
block dependent claims and continue independent work. Reuse unaffected checks.

Environment: Python 3.12, standard-library-only kit, supplied separately as a
clean checkout. Set `DEV_GUARDRAIL_KIT` to that external absolute path and
`DEV_GUARDRAIL_REVISION` to the full reviewed commit. The kit is a correction
implementation, not the source of principles. Keep all records outside this
checkout; no kit files or private context may be committed here.

Normal invocation (TASK is an existing private or temporary directory):

```sh
npm run dev:task -- route --request "$TASK/request.json" --policy "$TASK/policy.json" --input "$TASK/canonical.json"
npm run dev:task -- authorize --request "$TASK/request.json" --input "$TASK/authorization.json"
npm run dev:task -- start --request "$TASK/request.json" --policy "$TASK/policy.json" --output "$TASK/started.json"
npm run dev:task -- complete --request "$TASK/request.json" --state "$TASK/started.json" --input "$TASK/completion.json" --output "$TASK/finished.json"
npm run dev:task -- status --request "$TASK/request.json" --state "$TASK/finished.json"
```

Use the reviewed kit's record interface: completion requires `canonical`, with
source identity/version/read evidence bound to the current instruction/session.
Identify Brain by that MCP retrieval route, not an invented note URL. If the
response supplies no version, label any computed content fingerprint and read
observation time explicitly; neither is a provider version or authenticated read.
Inspect `result`, `next_step`, blocked and independent paths. Partial routing
returns successfully so independent work can continue; it is not completion.
Use `revise` with a new request/policy, prior `--state` and fresh `--output` when
instructions change. Review necessity and applicable checks using actual evidence.
Do not infer source authenticity or semantic truth from a filled schema.
This adapter never executes actions, grants permission, or verifies production.

Tests: `python3.12 -B -m unittest discover -s tests -p 'test_dev_task.py' -v`.
Set `DEV_TASK_TEST_INPUTS` to external synthetic request/policy/completion JSON
compatible with the reviewed kit. Tests call the real adapter and kit; synthetic
records are not project-canonical evidence. Publication and deployment require
the applicable existing authorization and safe route.
