# Customer validation plan

This plan is for future conversations with Forgejo operators. No outreach or interview has happened yet.

## Who to learn from

Interview self-hosters and small organizations that administer their own Forgejo backups. Include people who have actually performed a restore and people who have only verified that backup jobs completed.

## Ask about past behavior

1. Tell me about the last time you had to recover Forgejo or prove a backup was usable.
2. What exact backup components and tools did you use? Where did the process get difficult?
3. How did you verify that repositories, issues, attachments, Actions secrets, and integrations worked after recovery?
4. What did the recovery or rehearsal cost in staff time, downtime, or risk?
5. What do you use now, and what would make you switch or add a tool?
6. Have you considered or built a disposable restore test? What does it fail to cover compared with your actual backup and deployment?
7. Who owns the recovery evidence, and when did they last pay for a restore drill, MSP support, or audit evidence? What budget and purchase process applied?
8. Would a Forgejo recipe for an existing restore runner meet the need, or do you require a dedicated service? What would still justify paying for help?
9. If a managed provider or MSP handles backups, what exactly does the contract promise for restore time and data loss? When did anyone last boot a restored Forgejo instance and verify a repository or database record, rather than only confirm that a backup job completed?
10. What private evidence can you show that the last restore test covered the same backup source, Forgejo version, database, repositories, and external storage you depend on?
11. Do you test every instance or rotate samples by recovery priority? How do you record the snapshot tested, the actual elapsed recovery time, manual fixes, and application-owner sign-off?
12. If an MSP offered a one-time Forgejo recovery-evidence review with an isolated restore drill and private report, who would buy it, what would it need to cover, and would a $395 starting price be reasonable or should this be included in an existing agreement?

Ask for a recent concrete example. Do not pitch the product before collecting the current workflow.

## Record evidence

For each conversation, record role and deployment scale only with consent; current backup/restore workflow; last restore date; failure or near miss; labor and downtime; existing alternatives; any budget owner; and a verbatim description of what would trigger a purchase. Do not record credentials, instance URLs, repository names, or customer data.

## Decision gates

- Continue only if several operators describe recent, costly restore uncertainty that their current tools do not address.
- Treat backup retention, snapshot availability, and successful app-level restore as separate provider claims; verify which are contractually promised and which have actually been tested.
- Build an isolated restore runner only after an operator agrees to a supervised pilot using an environment and backup they are authorized to use.
- Stop or reposition if existing generic tools fully solve the problem or operators have no budget or urgency.
- Do not infer an unmet market from a provider having no contractual RTO alone; confirm that the buyer needs an independent restore drill and will pay for it.
- Treat verbal interest as discovery evidence, not revenue. Count revenue only after an actual paid pilot.
- Keep the tool open source; test paid support or supervised drills before hosted processing.
