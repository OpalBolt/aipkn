# Tag Taxonomy

| Tag | Meaning |
|---|---|
| `#ai` | Artificial intelligence, LLMs, agents |
| `#dev` | Software development, code, architecture |
| `#ops` | Infrastructure, DevOps, tooling |
| `#career` | Professional development, job, skills |
| `#learning` | Study material, courses, books |
| `#personal` | Personal life, non-work |
| `#business` | Business strategy, work context |
| `#needs-review` | Requires user input before finalizing |
| `#archived` | No longer active or relevant |

## Expansion policy
A file agent may introduce a new topic tag if no existing tag fits. It declares the tag and definition in the `new_tags` staging field. The `commit_staging` module appends new tags here — agents never write to this file directly.
