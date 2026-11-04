# Batch / stage summary (paste into the project's handoff or reports folder)

```
Stage: <number and name>            Batch: <id>            Date: <iso>            Agent: <name>
Goal: <one line>        Rubric items targeted: <IDs>

Changes
- files moved/renamed: <n>   split: <n>   deleted: <n> (<MB>)   prefabs created: <n>   scenes touched: <list>
- tools used: <script + args>   proof files: <paths>

Gates (value | baseline | verdict)
- G1 compile: 0 errors
- G2 EditMode: PASS <n> | <n> ; SKIP <n> | <n>
- G3/G4 missing scripts / references: <n> | 0
- G6 Play 5 s: <scenes> console <empty|list>
- G9 perf: draw calls <n> | <n>; SetPass <n> | <n>; load <s> | <s>   (device measurement: yes/no)
- G10 lean: Assets <MB> | <MB>; unreferenced <MB> | <MB>; packages unused <n> | <n>

Rubric score: verified <x%> -> <y%>; pessimistic <x%> -> <y%>
Failed IDs now: <list>      U IDs checked this batch: <list>      New failures: <none|list>

Not verified: <honest list>
Decisions / rulings made: <one line each>
Next batch: <what, which files, acceptance numbers>
Lessons for the skills: <one line each or none>
```
