# Follow-up: trim the "deliberate trade-off" prose from the RWM concept page

**Status:** WIP, tracking only. Awaiting upstream merges.
**Blocked by:** [#184](https://github.com/datajoint/datajoint-docs/pull/184), [#185](https://github.com/datajoint/datajoint-docs/pull/185)

## What

Remove the "deliberate trade-off" prose from
`src/explanation/relational-workflow-model.md` and replace it with a short
sentence and a link to `comparison-to-workflow-languages.md`.

## Why

After [#184](https://github.com/datajoint/datajoint-docs/pull/184) (expanded
RWM intro) and [#185](https://github.com/datajoint/datajoint-docs/pull/185)
(new deeper pages) both land, the same argument lives in two places:

- RWM page: "The deliberate trade-off" subsection (introduced by #184).
- Comparison page: a more developed treatment with concrete comparators
  and the convertibility framing (introduced by #185).

Keeping both creates drift risk and dilutes the overview page. The
comparison page is the natural home for the developed argument; the RWM
page should mention the trade-off briefly and link out.

## How (rough outline)

1. Open `src/explanation/relational-workflow-model.md` (post-#184 state).
2. Locate the section beginning with the heading that introduces the
   "deliberate trade-off" framing (a few paragraphs near the top half of
   the page after the opening + four-shifts).
3. Replace the subsection with a single tight paragraph along these lines:
   - DataJoint accepts coupling deliberately, in exchange for one formal
     system across data structure, computation, dependencies, and integrity.
   - Link out: "see
     [Comparison to Workflow Languages](comparison-to-workflow-languages.md)
     for the structural treatment, what file-based workflows and task
     orchestrators offer, what each omits, and when to use them together."
4. Verify the surrounding flow still reads cleanly (the "Substrate
   consequences" section should follow naturally).
5. Run docs build locally (`mkdocs serve`) to check rendering.

## Out of scope

- No content moves in either direction other than the trim.
- No nav changes.
- No edits to other concept pages.

## Pick-up checklist

- [ ] #184 merged to `main`
- [ ] #185 merged to `main`
- [ ] Rebase this branch onto `main`
- [ ] Apply the trim per outline above
- [ ] Delete this tracker file as part of the same commit
- [ ] Move the PR out of draft and request review
