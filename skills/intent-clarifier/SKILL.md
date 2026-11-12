---
name: intent-clarifier
description: "Use ONLY when the owner asks to be questioned ('hoi toi', 'help me think', 'I cannot explain it') or a wrong guess would waste a day: build a written Intent Document through short question rounds, then confirm."
triggers: clarify, intent, help me think, hoi toi, lam ro y tuong, toi khong biet dien dat, underspecified, ambiguous, intent document
---

# Intent clarifier

The studio default is to decide and record a `Ruling:` line, not to stall on questions (`coding-discipline-karpathy`). Use this skill only when the owner invites questions, struggles to put an idea into words, or the request has several readings and a wrong pick is expensive (new mechanic, economy shape, clone scope). Idea source: FakeMG/ai-instructions `intent-clarifier`, adapted.

## Intent Document (the deliverable, markdown)
1. **Definition and look**: what it is, parts, how it looks and feels, core identity.
2. **Boundaries**: scope limits, hard constraints, what it is NOT.
3. **Execution**: step-by-step walkthrough of each interaction or scenario.

## Round protocol
1. Ask 3-5 targeted questions grouped by document section (what, why, how, context, edge cases). Offer a recommended answer to each so a one-word reply is enough.
2. Reflect a draft document back; mark uncertain parts and propose a best guess for each.
3. Test with short true/false claims ("the cash drops only when the pet is hit, true?").
4. Revise only the parts that changed. Repeat until the owner agrees.

## Make answering easy
Offer an analogy, a concrete example, a counter-example, a screenshot/sketch request, or "what would you check first?". The owner is a feel-first developer: prefer examples and references over abstract definitions.

## Stop conditions
- The owner confirms the document is accurate: print it once in a code block, say `Shall I proceed with this understanding?` in the owner's language, then continue with `spec-then-plan` (do not restart the questions).
- The owner is frustrated or says skip: stop asking, state the key assumptions as `Ruling:` lines, and proceed.
