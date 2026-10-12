# AGENT RULES

---

## DO

- DO: give each agent one clear job. Write down its goal, its tasks, and its limits before you build it.
- DO: give only the access it needs. If the agent only needs to read, do not let it write.
- DO: ask a human before risky actions. Get a "yes" first for things you cannot undo, like deleting data, sending emails, or moving money.
- DO: give clear context. Use simple structure (like Markdown or JSON). Put the most important information first.
- DO: log every tool call and action. Save the inputs, outputs, and tools used, so you can find problems later.
- DO: test the agent often (evals). Check it against a set of good example answers, mainly after you change the system prompt.
- DO: ask the user when something is not clear — the goal, the scope, what parts are affected, or what should happen. Never guess.
- DO: write in basic English. Many users and developers do not speak English well. This is for all text: chat messages, questions, plans, prompts to sub-agents, reviews, reports, and docs.
- DO: write short sentences. One idea per sentence.
- DO: use common words. Say "use", not "leverage". Say "check", not "validate". Say "change", not "modify". Say "show", not "surface". Say "split", not "decompose". Say "start", not "initiate". Say "about", not "regarding". Say "enough", not "sufficient".
- DO: explain rare technical words in a few words the first time you use them. Common ones (API, cache, token, migration, …) are fine.
- DO: use lists and tables instead of long paragraphs.
- DO: say who does the action: "The API returns an error", not "An error is returned by the API".
- DO: say the main point first (what happened or what is needed). Then give the details.

---

## DO NOT

- DON'T: give unclear instructions like "be helpful". The agent will then do things you do not expect.
- DON'T: give full or admin access. If someone attacks the agent, the damage will be much bigger.
- DON'T: let the agent work with no human checking it, mainly in the first 30 days.
- DON'T: send too much raw data at once. It fills the context window, and the agent may start to make things up.
- DON'T: hide failures. If the agent fails, it must tell a human. It must not guess or keep going when something is broken.
- DON'T: think the first setup is final. Agents and models change over time. Keep updating the limits based on real results.
- DON'T: change anything the user did not ask for.
- DON'T: read secrets, like keys, certificates, or passwords.
- DON'T: read values in environment files or environment variables. You may read only the key names.
- DON'T: add Claude as a co-author (e.g. a `Co-Authored-By: Claude` line or a "Generated with Claude Code" line) in any commit message or PR description.
- DON'T: use idioms, slang, or fancy words (e.g. "low-hanging fruit", "boil the ocean", "holistic", "synergy", "robust", "seamless").
- DON'T: write a long paragraph when a short list works.
- DON'T: say the same thing twice in different words.
