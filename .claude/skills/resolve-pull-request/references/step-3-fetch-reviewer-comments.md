# Step 3 — Fetch Reviewer Comments

Get **every review comment** on the PR. Use the method you chose in Step 1. You need:

- Inline comments (on a file + line)
- Review summary texts
- If each thread is resolved or not

## Using MCP

Use the MCP tools to list the PR's review comments / threads. For each comment, save:

- Comment / thread ID (Step 6 needs it to reply and resolve)
- File path and line
- Author and text
- Thread state: **resolved** or **unresolved**. Also if it is **outdated** (its line no longer exists)

## Using the CLI

| Platform  | List inline review comments                                            | Review summary bodies / thread state                                             |
| --------- | ---------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| GitHub    | `gh api repos/{owner}/{repo}/pulls/{number}/comments --paginate`       | `gh pr view <number> --json reviews`; resolved state via GraphQL `reviewThreads` |
| GitLab    | `glab api projects/:id/merge_requests/<number>/discussions --paginate` | `resolved` / `resolvable` fields are on each discussion note                     |
| Bitbucket | `bb pr comments <number>` (flags vary by CLI)                          | per-CLI                                                                          |

**GitHub — thread IDs and resolved state (GraphQL):** A REST comment ID cannot resolve a thread. You need the thread node ID.

```bash
gh api graphql -f query='
  query($owner:String!,$repo:String!,$number:Int!){
    repository(owner:$owner,name:$repo){
      pullRequest(number:$number){
        reviewThreads(first:100){
          nodes{ id isResolved isOutdated
            comments(first:50){ nodes{ id databaseId path line body author{login} } } } } } } }' \
  -F owner=<owner> -F repo=<repo> -F number=<number>
```

## Using the browser

Open the PR page. Read the comment threads on the **Conversation** tab (GitHub) or the **Overview** / **Activity** tab (GitLab, Bitbucket). Read the page as text where you can.

- Open hidden threads too. For example, click "Show resolved" or "Load more" on GitHub.
- A thread marked **Outdated** is outdated. A collapsed thread marked **Resolved** is resolved.
- The browser does not show thread IDs. So for each comment, save the file, line, author, and the first words of the text. Step 6 uses these to find the thread again.

From the comments, find out:

- The file and line of each comment
- Who wrote each comment. A comment from the PR author is usually a note, not a request.
- Which threads are already **resolved** or **outdated**. You may skip these in Step 4.

> Save each comment's ID (if you have one), file, line, author, text, and resolved/outdated state. Step 6 needs these to reply and resolve. Keep them until the end.
